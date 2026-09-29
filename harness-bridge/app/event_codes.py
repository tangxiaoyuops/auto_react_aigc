"""SSE 事件构造：与 cognition-plane 输出协议一致，供 session_service 原样消费。"""
from __future__ import annotations

from typing import Any, Dict


def reasoning_content(content: str) -> Dict[str, Any]:
    return {"type": "REASONING_CONTENT", "data": {"content": content, "node_name": "思考"}}


def text_message(content: str) -> Dict[str, Any]:
    return {"type": "TEXT_MESSAGE_CONTENT", "data": {"content": content, "node_name": "回答"}}


def run_end(run_id: str, total_duration: int = 0) -> Dict[str, Any]:
    return {"type": "RUN_END", "data": {"run_id": run_id, "total_duration": total_duration}}


def run_error(error: str) -> Dict[str, Any]:
    return {"type": "RUN_ERROR", "data": {"error": error}}


def user_message(content: str) -> Dict[str, Any]:
    """模拟一条用户消息转写(供前端可见),当前仅作占位。"""
    return {"type": "USER_MESSAGE_CONTENT", "data": {"content": content}}


def serialize(event: Dict[str, Any]) -> str:
    """SSE 序列化：data: <json>"""
    import json
    return "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"