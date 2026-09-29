"""Skill 文件树模型（对应 Cursor/Claude 风格的文件夹式 Skill）。

一个 Skill 是一棵文件树，默认包含：
  SKILL.md          - 主说明（name/description frontmatter + 指引）
  references.md     - 参考资料（可被装载进上下文的详细文档）
  analysis.md       - 分析口径/归因说明
  fields.md         - 字段/指标口径定义
  scripts/          - 可执行的 Python 脚本（可被 Agent 经 subprocess 运行）

存储策略（hybrid）：
  - 文本文件（md 等）保存在 DBResource.meta["files"] 的 JSON 文件树中（统一编辑、统一装载）。
  - Python 脚本（scripts/*.py）在上述文件树中保存，同时由 SkillFileStore 同步写到磁盘工作区，
    供 cognition 层 run_skill_script 工具以 subprocess 隔离执行。
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# Skill 文件树 meta 键
FILES_KEY = "files"        # meta[files] = { "SKILL.md": "...", "scripts/x.py": "...", ... }
DEFAULT_SKILL_MD = """---
name: {name}
description: {description}
---
# {name}

## 用途
在此描述该 Skill 的能力与触发场景。

## 操作指引
在此给出执行步骤、要点与输出规范。

## 关联资源
- 详细参考见 [references.md](references.md)
- 字段口径见 [fields.md](fields.md)
- 分析口径见 [analysis.md](analysis.md)
- 可执行脚本见 [scripts](scripts/)
"""

DEFAULT_REFERENCES_MD = "# 参考资料\n\n此处存放该 Skill 需要的详细背景、SQL 样例、流程文档等。\n"
DEFAULT_ANALYSIS_MD = "# 分析口径\n\n此处说明指标归因、对比周期、结论输出规范等。\n"
DEFAULT_FIELDS_MD = "# 字段口径\n\n此处定义该 Skill 涉及指标的字段名、类型、单位与计算逻辑。\n"
DEFAULT_SCRIPT_PY = '''\
"""示例脚本：Skill 的可执行 Python 脚本。

Agent 可通过运行 `scripts/<本文件名>` 调用本脚本。
请在入口处定义 main，接收字符串参数，返回结构化输出。
"""
import json
import sys
from typing import List


def main(argv: List[str]) -> dict:
    # 在此实现业务逻辑
    return {"ok": True, "args": argv}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1:]), ensure_ascii=False, indent=2))
'''


def default_files(name: str, description: str) -> Dict[str, str]:
    """生成一个新 Skill 的默认文件树（含一个可执行示例脚本）。"""
    files = {
        "SKILL.md": DEFAULT_SKILL_MD.format(name=name, description=description or ""),
        "references.md": DEFAULT_REFERENCES_MD,
        "analysis.md": DEFAULT_ANALYSIS_MD,
        "fields.md": DEFAULT_FIELDS_MD,
    }
    files.update(default_script_files())
    return files


def default_script_files() -> Dict[str, str]:
    """生成默认脚本目录示例。"""
    return {
        "scripts/example.py": DEFAULT_SCRIPT_PY,
    }


def is_script_path(path: str) -> bool:
    """判断一个文件路径是否为可执行脚本（scripts/ 下的 .py）。"""
    parts = path.replace("\\", "/").split("/")
    return len(parts) >= 2 and parts[0] == "scripts" and path.endswith(".py")


def file_tree_keys(files: Dict[str, str]) -> List[str]:
    """返回文件树全部路径（'/' 规范化）。"""
    return sorted(files.keys())


def normalize_path(path: str) -> str:
    """规范化文件路径：统一斜杠、去除 './'、阻止路径穿越。"""
    p = path.replace("\\", "/").strip().lstrip("./")
    if ".." in p.split("/"):
        raise ValueError(f"非法路径: {path}")
    return p