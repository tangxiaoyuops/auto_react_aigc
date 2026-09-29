"""验证 Skill 文件存储 + 脚本执行（不再依赖 FastAPI/DB，直接测核心逻辑）。

用法：在仓库根目录执行
    python -m scripts.test_skill_store
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "control-plane"))

# 隔离磁盘工作区
_TMP = tempfile.mkdtemp(prefix="skill_store_test_")
os.environ["SKILLS_WORKSPACE"] = _TMP

from app.services.skill_file_service import SkillFileStore, SKILLS_WORKSPACE  # noqa: E402
from shared.schemas.skill_file import default_files, is_script_path  # noqa: E402


class FakeResource:
    def __init__(self, rid, name):
        self.id = rid
        self.name = name
        self.meta = {}
        self.updated_at = None


def main():
    failed = 0

    def check(cond, msg):
        nonlocal failed
        if cond:
            print(f"  PASS: {msg}")
        else:
            print(f"  FAIL: {msg}")
            failed += 1

    # 1) default_files 生成 Cursor 风格结构
    print("== default_files ==")
    files = default_files("metrics-turnover-rate", "人力离职率指标查询")
    check(all(k in files for k in ("SKILL.md", "references.md", "analysis.md", "fields.md")),
          "生成 SKILL.md/references/analysis/fields")
    check("scripts/example.py" in files, "包含可执行示例脚本 scripts/example.py")
    check("## 操作指引" in files["SKILL.md"], "SKILL.md 含操作指引")

    # 2) 落盘脚本（hybrid 磁盘侧）
    print("== 落盘脚本 ==")
    store = SkillFileStore(None)
    files["scripts/analyze.py"] = 'import sys\nprint("demo:" + sys.argv[1])\n'
    r = FakeResource("r1", "metrics-turnover-rate")
    store._sync_scripts_to_disk(r.id, r.name, files)
    wsdir = SKILLS_WORKSPACE / "metrics-turnover-rate" / "scripts" / "analyze.py"
    check(wsdir.exists() and "demo:" in wsdir.read_text(encoding="utf-8") if wsdir.exists() else False,
          "脚本写入磁盘工作区")
    # 非脚本不落盘
    check(not (SKILLS_WORKSPACE / "metrics-turnover-rate" / "SKILL.md").exists(),
          "非脚本文件不落盘")

    # 3) 编辑器 run 端点逻辑（run_skill_script_python，与端点共用同一实现）
    print("== run 端点 ==")
    from app.services.skill_file_service import run_skill_script_python
    res = run_skill_script_python("metrics-turnover-rate", "analyze.py", ["OK"])
    check(res["success"] and "demo:OK" in res["output"], f"run 输出 -> {res.get('output')!r}")
    bad = run_skill_script_python("metrics-turnover-rate", "../evil.py", [])
    check(not bad["success"], "路径穿越被拦截（端点）")

    print("\n==== 结果 ====")
    if failed == 0:
        print("ALL TESTS PASSED")
        return 0
    print(f"{failed} test(s) FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())