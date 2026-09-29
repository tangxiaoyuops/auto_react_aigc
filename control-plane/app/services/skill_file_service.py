"""Skill 文件存储服务（hybrid）：DB meta 文件树 + 磁盘脚本工作区。

职责：
  - 新增/读取/更新/删除 Skill 资源时，维护 meta["files"] 文件树。
  - 将 scripts/*.py 同步到磁盘工作区（SKILLS_WORKSPACE/<resource_id>/），
    使 cognition 层 run_skill_script 工具能通过 subprocess 隔离执行。
  - 校验文件路径，杜绝路径穿越。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import DBResource
from shared.schemas.skill_file import (
    is_script_path,
)


def _datetime_now():
    from datetime import datetime
    return datetime.utcnow()


# 磁盘工作区根目录：默认指向仓库根目录下的 skills_workspace，
# 使 control-plane 与 cognition-plane 共享同一套脚本目录。
# （可被环境变量 SKILLS_WORKSPACE 覆盖，便于测试隔离）
_REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS_WORKSPACE = Path(os.environ.get("SKILLS_WORKSPACE", str(_REPO_ROOT / "skills_workspace"))).resolve()


class SkillFileStore:
    """Skill 文件树的读取与落盘。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- 磁盘路径 ----------

    @staticmethod
    def skill_dir(dir_key: str) -> Path:
        """磁盘技能目录。dir_key 用技能名（resource.name），运行时才能按名字找到脚本。"""
        key = "".join(c for c in dir_key if c.isalnum() or c in "-_.")
        return SKILLS_WORKSPACE / key

    def ensure_skill_dir(self, dir_key: str) -> Path:
        d = self.skill_dir(dir_key)
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ---------- 落盘脚本 ----------

    def _sync_scripts_to_disk(self, resource_id: str, name: str, files: Dict[str, str]) -> None:
        """把文件树中所有 scripts/*.py 写入磁盘工作区（按 skill 名分目录）。"""
        root = self.ensure_skill_dir(name)
        for path, content in files.items():
            if not is_script_path(path):
                continue
            target = (root / path).resolve()
            # 安全护栏：必须位于 skill 目录内
            if not str(target).startswith(str(root.resolve())):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    def cleanup_skips(self, name: str) -> None:
        """移除该 Skill 的磁盘脚本工作区（删除资源时调用，容错）。"""
        d = self.skill_dir(name)
        try:
            if d.exists():
                import shutil
                shutil.rmtree(d)
        except Exception:
            pass

    # ---------- 文件树读取 ----------

    @staticmethod
    def get_files(resource) -> Dict[str, str]:
        meta = resource.meta or {}
        files = meta.get("files")
        if isinstance(files, dict):
            return files
        return {}

    async def get_resource(self, user_id: str, resource_id: str):
        result = await self.db.execute(
            select(DBResource).where(
                DBResource.id == resource_id, DBResource.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_resource_for_internal(self, resource_id: str):
        """内部查询：仅按 id 查（供认知层等内部服务拉取 Skill 包）。"""
        result = await self.db.execute(
            select(DBResource).where(DBResource.id == resource_id)
        )
        return result.scalar_one_or_none()

    def get_file_content(self, resource, path: str) -> Optional[str]:
        """取单个文件内容；不存在返回 None。"""
        files = self.get_files(resource)
        return files.get(path)

    def list_files(self, resource) -> List[str]:
        """返回文件树路径列表（scripts 子目录置顶排序）。"""
        files = self.get_files(resource)
        return sorted(files.keys())

    # ---------- 更新文件（通用） ----------

    async def read_file(self, user_id: str, resource_id: str, path: str) -> Optional[str]:
        res = await self.get_resource(user_id, resource_id)
        return self.get_file_content(res, path) if res else None

    async def write_files(self, resource, files: Dict[str, str]) -> Dict[str, str]:
        """整体覆盖文件树并同步脚本到磁盘（按技能名分目录）。"""
        resource.meta = {**(resource.meta or {}), "files": files}
        resource.updated_at = _datetime_now()
        await self.db.commit()
        await self.db.refresh(resource)
        self._sync_scripts_to_disk(resource.id, resource.name, files)
        return files


def _validate_and_resolve(skill_name: str, script: str):
    """校验脚本名与路径，返回可执行的目标 Path；非法返回 (None, error)。"""
    rel = script.replace("\\", "/").strip()
    if rel.startswith("scripts/"):
        rel = rel[len("scripts/"):]
    if not rel.endswith(".py") or not rel or "/" in rel or rel in (".", ".."):
        return None, f"非法脚本名: {script}"
    key = "".join(c for c in skill_name if c.isalnum() or c in "-_.")
    root = SKILLS_WORKSPACE / key
    target = (root / "scripts" / rel).resolve()
    if not str(target).startswith(str((root / "scripts").resolve())):
        return None, f"脚本越权: {script}"
    if not target.exists():
        return None, f"脚本不存在: scripts/{rel}"
    return target, None


def run_skill_script_python(skill_name: str, script: str, args: list, timeout: float = 20.0) -> dict:
    """执行 Skill 磁盘工作区中的脚本（subprocess 隔离），返回 stdout/stderr/退出状态。

    供 control-plane 技能编辑器的「运行」按钮与认知层 run_skill_script 工具共用同一套
    安全校验（白名单脚本名 + 目录护栏，杜绝路径穿越）。

    注意：这是同步阻塞版本（内部管理事件循环），仅在无运行中事件循环的线程里调用
    （如认知层工具）。FastAPI 异步路由请调用 run_skill_script_async。
    """
    import asyncio

    target, err = _validate_and_resolve(skill_name, script)
    if err:
        return {"success": False, "error": err}

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(asyncio.to_thread(_run_subprocess, target, args, timeout))
    finally:
        loop.close()


async def run_skill_script_async(skill_name: str, script: str, args: list, timeout: float = 20.0) -> dict:
    """异步执行 Skill 脚本（供 FastAPI async 路由调用，避免阻塞事件循环）。"""
    import asyncio

    target, err = _validate_and_resolve(skill_name, script)
    if err:
        return {"success": False, "error": err}
    return await asyncio.to_thread(_run_subprocess, target, args, timeout)


def _run_subprocess(target: Path, args: list, timeout: float):
    import subprocess
    import sys
    try:
        proc = subprocess.run(
            [sys.executable, str(target), *args],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(target.parent),
        )
        out = (proc.stdout or "")[-8000:]
        if proc.stderr:
            out += f"\n[stderr]\n{(proc.stderr or '')[-4000:]}"
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "output": out,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"执行超时（>{timeout}s）"}
    except Exception as e:
        return {"success": False, "error": str(e)}