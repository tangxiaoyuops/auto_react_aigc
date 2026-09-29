"""集成测试：认知层 load_skills_async 从 control-plane 拉取自定义 Skill。

用法：在 cognition-plane 目录执行
    python ../scripts/test_skill_loader.py
"""
import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "cognition-plane"))
os.environ.setdefault("CONTROL_PLANE_URL", "http://localhost:8081")


async def main():
    failed = 0

    def check(cond, msg):
        nonlocal failed
        if cond:
            print(f"  PASS: {msg}")
        else:
            print(f"  FAIL: {msg}")
            failed += 1
        return cond

    from app.skills.loader import load_skills_async

    # 1) 内置 skill：sk1（数据分析）应该命中本地注册表
    print("== 内置 skill ==")
    b1 = await load_skills_async(["sk1"])
    check(len(b1.skill_defs) == 1, "内置 sk1 装载成功")
    check("数据分析" in b1.render_system_prompt() or "经营数据分析" in b1.render_system_prompt(),
          "sk1 提示词已注入")

    # 2) 自定义 skill：circturnover（DB 资源，走 HTTP 拉取）
    print("== 自定义 skill（HTTP 拉取） ==")
    b2 = await load_skills_async(["baefc427-e705-4572-9216-d47d764498e1"])
    check(len(b2.skill_defs) == 1, "自定义 skill 装载成功")
    names = [d.name for d in b2.skill_defs]
    check("circturnover" in names, f"skill 名为 circturnover, got {names}")
    prompt = b2.render_system_prompt()
    check("circturnover" in prompt, "SKILL.md 已注入提示词")
    check("run_skill_script" in b2.tools, f"run_skill_script 已挂载, tools={b2.tools}")

    # 3) 不存在的 id：静默跳过
    print("== 不存在 id ==")
    b3 = await load_skills_async(["not-exist-id-12345"])
    check(len(b3.skill_defs) == 0, "未知 id 静默跳过")

    # 4) 空列表
    b4 = await load_skills_async([])
    check(len(b4.skill_defs) == 0 and b4.render_system_prompt() == "", "空列表返回空 bundle")

    # 5) run_skill_script 工具执行（共享工作区）
    print("== run_skill_script 执行 ==")
    from app.tools.executor import ToolExecutor
    from app.tools import builtin as _builtin  # noqa: F401 触发注册
    ex = ToolExecutor()
    r = await ex.execute("run_skill_script", {
        "skill_name": "circturnover", "script": "analyze.py", "args": ["HR"],
    })
    check(r.get("success") and r.get("result", {}).get("success"),
          f"脚本执行成功 -> {r.get('result', {}).get('stdout')!r}")

    # 6) 自定义 skill 专属工具（skill_name 预绑定）
    print("== 专属脚本工具 ==")
    b6 = await load_skills_async(["baefc427-e705-4572-9216-d47d764498e1"])
    names = [td.name for td in b6.tool_defs]
    check("run_circturnover_script" in names, f"专属工具名正确 -> {names}")
    if names:
        td = b6.tool_defs[0]
        schema = td.to_schema()
        check("script" in schema["function"]["parameters"]["properties"],
              "专属工具 schema 只暴露 script/args")
        # 执行专属工具
        r6 = await td.fn(script="analyze.py", args=["HR"])
        check(r6.get("success") and "ANALYZE_OK" in (r6.get("stdout") or ""),
              f"专属工具执行成功 -> {r6.get('stdout')!r}")

    print("\n==== 结果 ====")
    if failed == 0:
        print("ALL TESTS PASSED")
        return 0
    print(f"{failed} test(s) FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))