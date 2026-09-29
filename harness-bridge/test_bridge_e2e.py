"""端到端验证：真实调用 harness headless（需 AIMP key）。

在 harness-bridge 目录执行：
    python -m test_bridge_e2e

会真实运行 harness headless 一次，打印解析出的 reasoning 与 answer。
"""
from __future__ import annotations

import asyncio
import os
import sys


def _load_key() -> str:
    key = os.environ.get("AIMP_OPENAI_API_KEY", "")
    if key:
        return key
    env_path = r"D:\projects\react_demo\auto_react_aigc\cognition-plane\.env"
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("AIMP_OPENAI_API_KEY="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        return ""
    return ""


async def main() -> int:
    from app.patch_builder import PatchGenerator
    from app.harness_runner import HarnessRunner

    key = _load_key()
    if not key:
        print("FATAL: 未配置 AIMP_OPENAI_API_KEY")
        return 1

    runspec = {
        "model": "qwen3-5-397b-a17b",
        "system_prompt": "你是一个企业订单助手，能用工具查询订单数据。",
        "tools": ["query_records", "aggregate_records"],
        "skills": [],
    }
    gen = PatchGenerator(
        aimp_api_base="https://aimpapi.midea.com/t-aigc/d-dban-qwen3-5-397b-a17b/v1",
        model=runspec["model"],
    )
    patch_path = gen.write_patch(runspec)
    print(f"patch written: {patch_path}")

    runner = HarnessRunner(
        harness_dir=r"D:\projects\deepseek_harness学习\deepseek-harness",
        patch_path=patch_path,
        message="用 query_records 工具查客户 Ada 的订单，并按区域汇总金额",
        env={"AIMP_OPENAI_API_KEY": key},
        timeout_s=180,
    )
    result = await runner.run()

    print("\n==== reasoning 块 ====")
    for i, r in enumerate(result.get("reasoning", [])):
        print(f"[{i}] {r[:200]}")
    print("\n==== answer ====")
    print(result.get("answer", "(empty)"))

    ans = (result.get("answer") or "").strip()
    # 错误信息/超时判失败；真实答案应含内容
    bad = ("无法启动" in ans or "超时" in ans or "失败" in ans)
    ok = bool(ans) and not bad
    print("\n" + ("E2E PASS (got valid answer)" if ok else "E2E FAIL (bad answer)"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))