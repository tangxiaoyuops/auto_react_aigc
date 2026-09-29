"""验证 Cordis 风格工具插件化层的核心行为。

用法：在 cognition-plane 目录下执行
    python -m test_tools_inventory
"""
import asyncio


async def main() -> int:
    # 先用临时工作区隔离，确保 run_skill_script 使用测试目录
    import os, tempfile
    os.environ["SKILLS_WORKSPACE"] = tempfile.mkdtemp(prefix="skill_tool_")
    from app.tools.base import inventory, ToolDef
    from app.tools.builtin import calculator, web_search, run_skill_script

    failed = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal failed
        if cond:
            print(f"  PASS: {msg}")
        else:
            print(f"  FAIL: {msg}")
            failed += 1

    # 1) 内置工具应已自动注册到全局 inventory
    print("== 注册 == ")
    names = inventory.names()
    check("calculator" in names, f"calculator 已注册 -> {sorted(names)}")
    check("web_search" in names, f"web_search 已注册 -> {sorted(names)}")
    check("run_skill_script" in names, f"run_skill_script 已注册 -> {sorted(names)}")

    # 2) schema 自动生成（含 required）
    print("\n== schema 生成 ==")
    schemas = inventory.schemas()
    schema_names = [s["function"]["name"] for s in schemas]
    check(len(schemas) == 3, f"生成 {len(schemas)} 个 schema")
    calc_schema = next(s for s in schemas if s["function"]["name"] == "calculator")
    calc_params = calc_schema["function"]["parameters"]
    check(calc_params["required"] == ["expression"], f"calculator required=[expression] -> {calc_params['required']}")
    check("num_results" not in calc_params["required"], "num_results 默认非必填")
    rs_schema = next(s for s in schemas if s["function"]["name"] == "run_skill_script")
    rs_params = rs_schema["function"]["parameters"]
    check({"skill_name", "script"} <= set(rs_params["required"]), "run_skill_script required=[skill_name, script]")

    # 3) ToolExecutor 能通过注册表执行（同进程，避免导入 app.agent 连锁依赖）
    print("\n== executor 执行 ==")
    from app.tools.executor import ToolExecutor
    ex = ToolExecutor()
    r1 = await ex.execute("calculator", {"expression": "1+2*3"})
    check(r1["success"] and r1["result"]["result"] == 7, f"calculator 1+2*3 = {r1['result']}")

    r2 = await ex.execute("web_search", {"query": "hello", "num_results": 3})
    check(r2["success"] and len(r2["result"]["results"]) == 3, f"web_search 返回 3 条 -> {len(r2['result']['results'])}")

    r3 = await ex.execute("not_exist", {})
    check(not r3["success"] and "not found" in r3["error"], f"未知工具报错 -> {r3['error']}")

    # 4) run_skill_script：在临时工作区落盘脚本后执行
    print("\n== run_skill_script 执行 ==")
    import os
    from pathlib import Path
    # SKILLS_WORKSPACE 已在 main 开头设置为临时目录
    skill = "metrics-turnover-rate"
    script_dir = Path(os.environ["SKILLS_WORKSPACE"]) / skill / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    (script_dir / "analyze.py").write_text(
        "import sys\nprint('OK:' + '+'.join(sys.argv[1:]))\n", encoding="utf-8"
    )

    r4 = await ex.execute("run_skill_script", {"skill_name": skill, "script": "analyze.py", "args": ["2024", "Q3"]})
    check(r4["success"] and "OK:2024+Q3" in r4["result"]["stdout"], f"执行脚本输出 -> {r4['result'].get('stdout')!r}")

    r5 = await ex.execute("run_skill_script", {"skill_name": skill, "script": "missing.py", "args": []})
    check(not r5["result"]["success"] and "不存在" in r5["result"]["error"], f"缺失脚本报错 -> {r5['result'].get('error')}")

    r6 = await ex.execute("run_skill_script", {"skill_name": skill, "script": "../evil.py", "args": []})
    check(not r6["result"]["success"], "路径穿越被拦截")

    print("\n==== 结果 ====")
    if failed == 0:
        print("ALL TESTS PASSED")
        return 0
    print(f"{failed} test(s) FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))