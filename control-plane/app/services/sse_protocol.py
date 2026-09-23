"""SSE 事件协议工具（对齐前端 Step 结构，即 'Trace Contract'）

前端消费的事件结构:
  Step { nodeType, nodeName, title, detail?, input?, result?, duration?, status }

后端推送事件类型:
  run_start      -> { run_id, session_id, agent_id }
  thought        -> Step(THOUGHT, detail)
  tool_call_start-> Step(TOOL, running)
  tool_call_end  -> Step(TOOL, success, input/result/duration)
  result         -> Step(RESULT, success)
  run_end        -> 结束标记
  error          -> Step(status: error)
"""
from typing import Any, Dict, Optional

# 事件类型常量
EVT_RUN_START = "run_start"
EVT_THOUGHT = "thought"
EVT_TOOL_CALL_START = "tool_call_start"
EVT_TOOL_CALL_END = "tool_call_end"
EVT_RESULT = "result"
EVT_RUN_END = "run_end"
EVT_ERROR = "error"

# 终结事件：SSE 流遇到这些类型应断开
TERMINAL_EVENTS = {EVT_RUN_END, EVT_ERROR}


def run_start_event(run_id: str, session_id: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
    """run_start 事件"""
    return {
        "type": EVT_RUN_START,
        "content": {"run_id": run_id, "session_id": session_id, "agent_id": agent_id},
    }


def thought_event(node_name: str, content: str) -> Dict[str, Any]:
    """thought 事件 -> Step(THOUGHT, running->success)"""
    return {
        "type": EVT_THOUGHT,
        "content": {
            "nodeType": "THOUGHT",
            "nodeName": node_name,
            "title": "思考中...",
            "detail": content,
            "status": "success",
        },
    }


def tool_call_start_event(tool_name: str, input_json: Any) -> Dict[str, Any]:
    """tool_call_start 事件 -> Step(TOOL, running)"""
    return {
        "type": EVT_TOOL_CALL_START,
        "content": {
            "nodeType": "TOOL",
            "nodeName": tool_name,
            "title": f"正在调用 {tool_name}...",
            "input": _stringify(input_json),
            "status": "running",
        },
    }


def tool_call_end_event(tool_name: str, output_json: Any, duration_ms: int) -> Dict[str, Any]:
    """tool_call_end 事件 -> Step(TOOL, success)"""
    return {
        "type": EVT_TOOL_CALL_END,
        "content": {
            "nodeType": "TOOL",
            "nodeName": tool_name,
            "title": f"{tool_name} 执行完成",
            "result": _stringify(output_json),
            "duration": duration_ms,
            "status": "success",
        },
    }


def result_event(content: str) -> Dict[str, Any]:
    """result 事件 -> Step(RESULT, success)"""
    return {
        "type": EVT_RESULT,
        "content": {
            "nodeType": "RESULT",
            "nodeName": "结果生成",
            "title": "生成最终回答",
            "detail": content,
            "status": "success",
        },
    }


def run_end_event(run_id: str, total_duration: int = 0) -> Dict[str, Any]:
    """run_end 结束事件"""
    return {
        "type": EVT_RUN_END,
        "content": {"run_id": run_id, "total_duration": total_duration},
    }


def error_event(message: str) -> Dict[str, Any]:
    """error 事件 -> Step(status: error)"""
    return {
        "type": EVT_ERROR,
        "content": {
            "nodeType": "ERROR",
            "nodeName": "执行失败",
            "title": "执行出错",
            "detail": message,
            "status": "error",
        },
    }


def _stringify(value: Any) -> str:
    """将入参/返回值转为可读字符串"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    import json
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except Exception:
        return str(value)
