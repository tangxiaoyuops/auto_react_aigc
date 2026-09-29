"""run_skill_script 工具：让 Agent 在 Skill 上下文中执行 Python 脚本。

设计（对应 hybrid 存储）：
  - Skill 的可执行脚本（scripts/*.py）由 control-plane 在保存时写入磁盘工作区
    SKILLS_WORKSPACE/<skill_name>/scripts/*.py。
  - 本工具以 subprocess 隔离执行目标脚本，返回 stdout/stderr/退出码，
    供 Agent 在 ReAct 多轮中读取执行结果继续推理。

安全隔离：
  - 脚本路径被限制在 skill 工作区目录内（杜绝路径穿越 / 越权执行）。
  - 使用 subprocess.run，超时兜底，异常捕获后转为结构化失败结果。
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from app.tools.base import tool, inventory

# 与 control-plane 共享的磁盘工作区：默认指向仓库根目录下的 skills_workspace
# （可由环境变量 SKILLS_WORKSPACE 覆盖，便于测试隔离）
_REPO_ROOT = Path(__file__).resolve().parents[4]
_SKILLS_WORKSPACE = Path(os.environ.get("SKILLS_WORKSPACE", str(_REPO_ROOT / "skills_workspace"))).resolve()


def _resolve_script(skill_name: str, script: str) -> Path:
    """把 skill_name + script 相对路径解析为工作区内的绝对路径；非法则抛 ValueError。"""
    # 允许传入 'scripts/a.py' 或 'a.py'；统一拼到 scripts/ 下
    rel = script.replace("\\", "/").strip()
    if rel.startswith("scripts/"):
        rel = rel[len("scripts/"):]
    if not rel.endswith(".py"):
        raise ValueError(f"仅支持执行 .py 脚本，收到: {script}")
    if not rel or "/" in rel or rel in (".", "..") or ".." in rel:
        raise ValueError(f"非法脚本名: {script}")
    root = _SKILLS_WORKSPACE / "".join(c for c in skill_name if c.isalnum() or c in "-_.")
    target = (root / "scripts" / rel).resolve()
    # 安全护栏：必须位于 skill 工作区 scripts/ 内
    if not str(target).startswith(str((root / "scripts").resolve())):
        raise ValueError(f"脚本越权（目标不在 skill 工作区）: {script}")
    return target


def _run_script(target: Path, args: list[str], timeout: int) -> dict:
    try:
        proc = subprocess.run(
            [sys.executable, str(target), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(target.parent),
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-8000:],
            "stderr": proc.stderr[-4000:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"脚本执行超时（>{timeout}s）"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@tool(
    name="run_skill_script",
    description=(
        "在指定 Skill 上下文中执行其 Python 脚本并返回执行结果。"
        "用于让 Agent 运行 Skill 携带的可执行分析脚本（如 scripts/ 下的 .py 文件）。"
    ),
    parameters={
        "skill_name": {"type": "string", "required": True, "description": "目标 Skill 名称，如 metrics-turnover-rate"},
        "script": {"type": "string", "required": True, "description": "脚本文件名，如 'analyze.py' 或 'scripts/analyze.py'"},
        "args": {
            "type": "array",
            "items": {"type": "string"},
            "description": "传递给脚本的命令行参数（字符串数组）",
        },
        "timeout": {"type": "number", "description": "执行超时秒数（默认 15）"},
    },
    output="脚本执行的 dict（stdout/stderr/returncode）",
)
async def execute(skill_name: str, script: str, args: list = None, timeout: float = 15.0) -> dict:
    try:
        target = _resolve_script(skill_name, script)
    except ValueError as e:
        return {"skill_name": skill_name, "script": script, "success": False, "error": str(e)}
    if not target.exists():
        return {
            "skill_name": skill_name, "script": script, "success": False,
            "error": f"脚本不存在: scripts/{target.name}（请先在 Skill 编辑器中保存脚本内容）",
        }
    result = await asyncio.to_thread(_run_script, target, args or [], float(timeout or 15))
    return {"skill_name": skill_name, "script": script, "success": result["ok"], **result}


inventory.register(execute)