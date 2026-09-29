"""端到端集成测试：创建 Skill -> 默认文件树 -> 读文件 -> 更新脚本 -> 运行脚本。

用法：在 control-plane 目录下执行
    python ../scripts/test_skill_api_integration.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "control-plane"))
os.environ["SKILLS_WORKSPACE"] = tempfile.mkdtemp(prefix="skill_api_")


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

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.db.database import Base
    from shared.schemas.resource import ResourceCreate

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.services.resource_service import ResourceService
    from app.services.skill_file_service import SkillFileStore, run_skill_script_async, SKILLS_WORKSPACE

    sid = Session()

    # 1) 创建 skill 资源 -> 默认文件树
    print("== 创建 Skill ==")
    svc = ResourceService(db=sid)
    create = ResourceCreate(type="skill", name="metrics-turnover-rate", description="人力离职率指标查询")
    resource = await svc.create_resource(user_id="u1", payload=create)
    store = SkillFileStore(db=sid)
    files = store.get_files(resource)
    check(all(k in files for k in ("SKILL.md", "references.md", "analysis.md", "fields.md", "scripts/example.py")),
          "创建后默认文件树就绪")
    check("## 操作指引" in files["SKILL.md"], "SKILL.md 含操作指引")

    # 2) 脚本已落盘到磁盘工作区
    print("== 脚本落盘 ==")
    script_path = SKILLS_WORKSPACE / "metrics-turnover-rate" / "scripts" / "example.py"
    check(script_path.exists(), "example.py 已写入磁盘工作区")

    # 3) 新增 custom 脚本并运行
    print("== 更新并运行脚本 ==")
    custom = 'import sys\nprint("TURNOVER:" + sys.argv[1])\n'
    files = {**files, "scripts/analyze.py": custom}
    await store.write_files(resource, files)
    disk_target = SKILLS_WORKSPACE / "metrics-turnover-rate" / "scripts" / "analyze.py"
    check(disk_target.exists() and "TURNOVER" in disk_target.read_text(encoding="utf-8"),
          "analyze.py 已落盘")

    res = await run_skill_script_async("metrics-turnover-rate", "analyze.py", ["HR"])
    check(res["success"] and "TURNOVER:HR" in res["output"], f"运行脚本 -> {res.get('output')!r}")

    # 4) 非法/穿越拦截
    bad = await run_skill_script_async("metrics-turnover-rate", "../evil.py", [])
    check(not bad["success"], "路径穿越拦截（run 助手）")
    bad2 = await run_skill_script_async("metrics-turnover-rate", "missing.py", [])
    check(not bad2["success"], "缺失脚本拦截")

    await sid.close()
    await engine.dispose()

    print("\n==== 结果 ====")
    if failed == 0:
        print("ALL TESTS PASSED")
        return 0
    print(f"{failed} test(s) FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))