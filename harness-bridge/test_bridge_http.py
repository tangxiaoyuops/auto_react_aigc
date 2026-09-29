"""验证 harness-bridge 的 FastAPI SSE 接口契约（用 TestClient，真实调 harness）。

用法：在 harness-bridge 目录执行
    python -m test_bridge_http
"""
from __future__ import annotations

import asyncio


async def main() -> int:
    try:
        from fastapi.testclient import TestClient
    except ImportError as e:
        print(f"缺依赖: {e}（需要 pip install httpx）")
        return 2

    import sys
    sys.path.insert(0, ".")

    # 需要在导入 app.main 前确保 key 可用
    import os
    key = os.environ.get("AIMP_OPENAI_API_KEY", "")
    if not key:
        env_path = r"D:\projects\react_demo\auto_react_aigc\cognition-plane\.env"
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("AIMP_OPENAI_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        break
        except OSError:
            pass

    from app.main import app

    client = TestClient(app)

    # health
    r = client.get("/health")
    print("health:", r.status_code, r.json())
    if r.status_code != 200:
        return 1

    # SSE execute
    payload = {
        "run_id": "test-run-1",
        "session_id": "s1",
        "message": "用 query_records 工具查客户 Ada 的订单",
        "model": "qwen3-5-397b-a17b",
        "tools": ["query_records"],
        "system_prompt": "你是企业订单助手",
    }
    print("\n== SSE 事件流 ==")
    event_types = []
    with client.stream("POST", "/api/v1/agent/execute/stream", json=payload) as resp:
        print("status:", resp.status_code)
        buf = ""
        for line in resp.iter_lines():
            if line.startswith("data: "):
                import json as _json
                ev = _json.loads(line[6:])
                et = ev.get("type")
                event_types.append(et)
                content = (ev.get("data") or {}).get("content") or ""
                print(f"  <{et}> {content[:80]}")

    print("\nevent types:", event_types)
    has_reason = any(t == "REASONING_CONTENT" for t in event_types)
    has_text = any(t == "TEXT_MESSAGE_CONTENT" for t in event_types)
    has_end = any(t == "RUN_END" for t in event_types)

    ok = has_reason and has_text and has_end
    print("\n" + ("HTTP TEST PASS (got reasoning+text+run_end)" if ok else "HTTP TEST FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))