"""Skill 生成与改写服务：借助 LLM（AIMP Qwen）产出 Skill 文件树内容。

两种动作：
  - generate：根据自然语言需求描述，从零生成一套 Skill 文件
    （SKILL.md + references.md + analysis.md + fields.md + scripts/*.py）。
  - rewrite：基于已有文件（current_files）改写指定目标文件（或整体完善）。

始终要求模型输出严格 JSON：{"files": {"<path>": "<content>", ...}}。
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.llm.gateway import LLMGateway


_DEFAULT_TEMPLATE = {
    "SKILL.md": """---
name: {name}
description: {description}
---

# {name}

## 用途
（一句话说明该 Skill 解决什么问题、何时使用）

## 能力
- 能力点 1
- 能力点 2
""",
    "references.md": """# 参考资料

补充领域背景、术语表、口径定义等，供模型理解。
""",
    "analysis.md": """# 分析方法

说明该 Skill 采用的算法、指标计算方式、结论生成流程。
""",
    "fields.md": """# 字段说明

本 Skill 涉及的输入/输出字段、以及各自含义与示例。
""",
}


_SYS_MSG = (
    "你是一名资深的数据分析垂直领域 Skill（技能包）设计专家。"
    "你会为用户的需求设计并输出一套结构完整、可直接落地的 Skill 文件。\n"
    "Skill 的典型文件树如下：\n"
    "  - SKILL.md：技能核心说明（YAML frontmatter 含 name/description，正文写明用途、能力、可调用的脚本）\n"
    "  - references.md：参考资料/术语/知识背景\n"
    "  - analysis.md：分析方法与算法说明\n"
    "  - fields.md：字段定义\n"
    "  - scripts/*.py：可被 Agent 通过 run_skill_script 调用的 Python 脚本（需含 main() 入口、打印 json）\n\n"
    "你的输出必须是**严格的单一 JSON 对象**，形如：\n"
    "{\"files\": {\"SKILL.md\": \"...\", \"scripts/analyze.py\": \"...\"}}\n"
    "除该 JSON 外不要输出任何解释、注释或 markdown 代码块包裹。"
)


def _strip_code_fence(text: str) -> str:
    """去掉可能包裹的 ```json ... ``` 围栏。"""
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z0-9]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def _parse_json(text: str) -> Optional[Dict[str, Any]]:
    """容错解析 LLM 输出。

    策略（按优先级）：
      1. 直接 json.loads（严格格式）；
      2. 剥离 ```json ... ``` 围栏后解析；
      3. 用 raw_decode 从左到右找首个合法 JSON 对象（容忍前后噪声）。
    """
    candidates = [text.strip()]
    fenced = _strip_code_fence(text)
    if fenced not in candidates:
        candidates.append(fenced)
    for cand in candidates:
        if not cand:
            continue
        try:
            data = json.loads(cand)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    # raw_decode 容错：扫描所有 '{' 起点，取第一个能解析出 dict 的片段
    decoder = json.JSONDecoder()
    idx = 0
    while True:
        start = text.find("{", idx)
        if start == -1:
            break
        try:
            obj, _ = decoder.raw_decode(text[start:])
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
        idx = start + 1
    return None


def _extract_files(data: Dict[str, Any]) -> Dict[str, str]:
    """从解析结果中提取 files 映射（兼容 files 缺失时整体当文件映射的兜底）。"""
    files = data.get("files")
    if isinstance(files, dict):
        return {str(k): str(v) for k, v in files.items()}
    return {str(k): str(v) for k, v in data.items() if not k.startswith("_")}


def _generate_prompt(description: str) -> List[Any]:
    user = (
        "请根据以下需求为业务场景设计并生成一套完整的 Skill 文件：\n"
        f"需求描述：{description}\n\n"
        "要求：\n"
        "1. 为 Skill 起一个简洁英文名（kebab-case）与准确中文描述。\n"
        "2. 至少包含 SKILL.md 与一个可执行的 scripts/analyze.py（含 main() 与 argparse/ sys.argv 参数）。\n"
        "3. 若场景涉及字段/算法/参考，补齐 references.md / analysis.md / fields.md。\n"
        "4. SKILL.md 需写清「用途/能力/如何调用脚本」。\n"
        "仅输出 JSON：{\"files\": {...}}\n"
    )
    return [SystemMessage(content=_SYS_MSG), HumanMessage(content=user)]


def _rewrite_prompt(description: str, current_files: Dict[str, str], target: str) -> List[Any]:
    file_brief = "\n".join(
        f"## {p}\n{content[:2000]}" for p, content in current_files.items()
    )
    if target and target != "all":
        user = (
            f"请改写当前 Skill 中 **{target}** 这一个文件，其它文件保持不变。\n"
            f"改写要求：{description}\n\n当前 Skill 文件如下：\n{file_brief}\n\n"
            "仅输出 JSON：{\"files\": {\"" + target + "\": \"改写后完整内容\"}}"
        )
    else:
        user = (
            f"请整体优化这套 Skill 文件，使其更完善、可直接落地。\n"
            f"优化要求：{description or '补齐缺口、提升可直接运行性'}\n\n当前文件：\n{file_brief}\n\n"
            "仅输出 JSON：{\"files\": {\"<path>\": \"<优化后内容>\", ...}}"
        )
    return [SystemMessage(content=_SYS_MSG), HumanMessage(content=user)]


async def assist_skill(
    action: str,
    description: str,
    current_files: Optional[Dict[str, str]] = None,
    target: str = "all",
    name_hint: str = "custom-skill",
    model: str = None,
) -> Dict[str, Any]:
    """执行 Skill 生成/改写，返回 {"files": {...}}。

    失败时返回 {"files": {}} 或抛异常由路由层转 502。
    """
    gateway = LLMGateway(model=model or None, temperature=0.3)
    current_files = current_files or {}
    if action == "rewrite":
        prompt_msgs = _rewrite_prompt(description, current_files, target)
    else:
        prompt_msgs = _generate_prompt(description or name_hint)

    reply = await gateway.ainvoke_json(prompt_msgs)
    text = reply.content if isinstance(reply.content, str) else json.dumps(reply.content, ensure_ascii=False)

    data = _parse_json(text)
    if not data:
        return {"files": {}, "raw": text[:500]}
    files = _extract_files(data)
    return {"files": files}