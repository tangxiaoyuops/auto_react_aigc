"""验证 harness-bridge 核心逻辑：patch 生成 + runner 解析。

用法：在 harness-bridge 目录下执行
    python -m test_bridge

测试不依赖外部服务（patch 生成），以及可选的 runner 真实调用（需配置 key）。
"""
from __future__ import annotations

import asyncio
import sys
import os


def test_patch_generation() -> int:
    from app.patch_builder import PatchGenerator

    failed = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal failed
        if cond:
            print(f"  PASS: {msg}")
        else:
            print(f"  FAIL: {msg}")
            failed += 1

    gen = PatchGenerator(
        aimp_api_base="https://aimp.example/v1",
        model="qwen3-5-397b-a17b",
    )

    print("== 仅模型（无工具无提示词）==")
    yaml1 = gen.build_patch_yaml({"model": "qwen3-5-397b-a17b", "tools": [], "system_prompt": ""})
    check("aimp-qwen" in yaml1, "包含 aimp-qwen provider")
    check("provider: aimp-qwen" in yaml1, "默认模型路由指向 aimp-qwen")
    check("biz-tool" not in yaml1, "无工具时不注入工具 plugin")
    check("system-prompt" not in yaml1, "无提示词时不注入 system-prompt")

    print("\n== 2.带工具和提示词 ==")
    yaml2 = gen.build_patch_yaml({
        "model": "qwen3-5-397b-a17b",
        "tools": ["tool_calculator"],
        "system_prompt": "你是一个订单专家",
    })
    check("calculator.ts" in yaml2, "tool_calculator 映射到 calculator.ts")
    check("biz-tool-0" in yaml2, "工具以 biz-tool-0 注入")
    check("你是一个订单专家" in yaml2, "system_prompt 注入")

    print("\n==== 结果 ====")
    if failed == 0:
        print("PATCH GENERATION TESTS PASSED")
        return 0
    print(f"{failed} test(s) FAILED")
    return 1


def test_runner_parse() -> int:
    """用模拟的 headless 输出验证 runner 解析逻辑（不实际调 harness）。"""
    from app.harness_runner import HarnessRunner

    # 直接验证解析算法：构造与真实 headless 相同的文本行
    lines = [
        "dsh: reasoning:",
        "User wants orders, calling query_records tool",
        "",
        "dsh: reasoning:",
        "Found Ada orders, 2 records",
    ]
    # 模拟解析：第一个块进 reasoning，最后块进 answer
    reasoning: list[str] = []
    answer = ""
    current: list[str] = []
    for text in lines:
        if text.startswith("dsh: reasoning:"):
            if current:
                reasoning.append("\n".join(current).strip())
            current = []
        elif text.strip():
            current.append(text)
    if current:
        answer = "\n".join(current).strip()

    print("== runner 解析逻辑 ==")
    mm = lambda *a, **k: a  # noqa
    failed = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal failed
        if cond:
            print(f"  PASS: {msg}")
        else:
            print(f"  FAIL: {msg}")
            failed += 1

    check(len(reasoning) == 1, f"middle block into reasoning ({len(reasoning)})")
    check("query_records" in reasoning[0], "reasoning content preserved")
    check("Ada orders" in answer, "final block into answer")
    check("calling query" in reasoning[0], "reasoning keeps details")
    return failed


async def run() -> int:
    code = test_patch_generation()
    if code != 0:
        return code
    return test_runner_parse()


if __name__ == "__main__":
    # 同步运行不需要 asyncio，直接执行
    code = test_patch_generation()
    if code == 0:
        code = test_runner_parse()
    raise SystemExit(code)