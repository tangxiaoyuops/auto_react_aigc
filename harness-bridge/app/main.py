"""harness-bridge：把 control-plane 的执行请求转发给 deepseek-harness(headless)。

对外暴露与 cognition-plane 相同的 SSE 接口：
  POST /api/v1/agent/execute/stream

这样 session_service._stream_from_cognition（control-plane 侧）无需改动，
只需把 COGNITION_URL 指向本服务即可。
"""
from __future__ import annotations

import os
import time
from typing import Dict, Any, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.event_codes import (
    reasoning_content,
    text_message,
    run_end,
    run_error,
    serialize,
)
from app.patch_builder import PatchGenerator
from app.harness_runner import HarnessRunner

app = FastAPI(title="harness-bridge", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 配置 ----------

DEFAULT_AIMP_BASE = "https://aimpapi.midea.com/t-aigc/d-dban-qwen3-5-397b-a17b/v1"
DEFAULT_MODEL = "qwen3-5-397b-a17b"

HARNESS_DIR = os.environ.get(
    "HARNESS_DIR",
    r"D:\projects\deepseek_harness学习\deepseek-harness",
)
# 企业模型 key：优先取进程环境，其次从 cognition-plane/.env 读取
_default_key = os.environ.get("AIMP_OPENAI_API_KEY", "")


def _load_cognition_key() -> str:
    """从 cognition-plane/.env 读取 AIMP key（未在环境变量提供时兜底）。"""
    if _default_key:
        return _default_key
    env_path = r"D:\projects\react_demo\auto_react_aigc\cognition-plane\.env"
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("AIMP_OPENAI_API_KEY="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


class ExecuteRequest(BaseModel):
    """与 cognition-plane 的 ExecuteRequest 对齐。"""
    run_id: str = ""
    session_id: str = ""
    message: str
    model: str = DEFAULT_MODEL
    tools: List[str] = []
    skills: List[str] = []
    system_prompt: Optional[str] = None


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "harness_dir": HARNESS_DIR}


@app.post("/api/v1/agent/execute/stream")
async def execute_stream(request: ExecuteRequest):
    async def event_generator():
        start = time.time()
        key = _load_cognition_key()
        if not key:
            yield serialize(run_error("未配置 AIMP_OPENAI_API_KEY"))
            return

        runspec: Dict[str, Any] = {
            "model": request.model or DEFAULT_MODEL,
            "system_prompt": request.system_prompt or "",
            "tools": request.tools or [],
            "skills": request.skills or [],
        }
        gen = PatchGenerator(aimp_api_base=DEFAULT_AIMP_BASE, model=runspec["model"])
        patch_path = gen.write_patch(runspec)
        try:
            runner = HarnessRunner(
                harness_dir=HARNESS_DIR,
                patch_path=patch_path,
                message=request.message,
                env={"AIMP_OPENAI_API_KEY": key},
                timeout_s=300,
            )
            result = await runner.run()

            # reasoning 块 → REASONING_CONTENT
            for reas in result.get("reasoning", []):
                if reas.strip():
                    yield serialize(reasoning_content(reas))

            # 最终答案
            answer = result.get("answer", "").strip()
            if answer:
                yield serialize(text_message(answer))

            dur = int((time.time() - start) * 1000)
            yield serialize(run_end(request.run_id, dur))
        except Exception as e:  # noqa: BLE001
            yield serialize(run_error(str(e)))
        finally:
            # 清理临时 patch 文件
            try:
                os.remove(patch_path)
            except OSError:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )