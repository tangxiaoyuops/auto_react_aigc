"""M4 接口冒烟测试：验证「六类可配置框架」后端链路。

覆盖 M1/M2/M3 新增能力：
  - 资源池 /resources/pool（读库）
  - 6 类资源 CRUD（含 tool）
  - Agent 挂载 tool/skill/prompt
  - Agent 编译 RunSpec（compile_runspec）

用法（控制平面已在 127.0.0.1:8080 运行）：
    python scripts/smoke_config_framework.py
退出码：全 PASS = 0，任一失败 = 1。
"""
import os
import json
import sys
import uuid

import requests

BASE = os.environ.get("CTRL_BASE", "http://127.0.0.1:8080/api/v1")
EMAIL = f"smoke_{uuid.uuid4().hex[:8]}@example.com"
PASSWORD = "password123"
USERNAME = f"smoke_user_{uuid.uuid4().hex[:6]}"

failed = 0


def check(cond: bool, msg: str):
    global failed
    if cond:
        print(f"  PASS: {msg}")
    else:
        print(f"  FAIL: {msg}")
        failed += 1


def main() -> int:
    s = requests.Session()

    # ---- 0. 注册 + 登录拿 token ----
    print("== 0. 认证 ==")
    r = s.post(f"{BASE}/auth/register", json={
        "email": EMAIL, "username": EMAIL.split("@")[0], "password": PASSWORD,
    })
    check(r.status_code in (200, 201, 409), f"register status={r.status_code}")
    r = s.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    check(r.status_code == 200, f"login status={r.status_code}")
    token = r.json().get("access_token")
    check(bool(token), "获取 access_token")
    s.headers["Authorization"] = f"Bearer {token}"

    # ---- 1. 资源池（M1：pool 读库 + 6 类） ----
    print("\n== 2. 资源池 pool ==")
    r = s.get(f"{BASE}/resources/pool")
    check(r.status_code == 200, f"pool status={r.status_code}")
    pool = r.json()
    check("tool" in pool and len(pool.get("tool", [])) > 0, "pool 含 tool 类别")
    check("skill" in pool and len(pool.get("skill", [])) > 0, "pool 含 skill")
    check("knowledge" in pool and len(pool.get("knowledge", [])) > 0, "pool 含 knowledge")

    # ---- 2. 创建 tool / skill / prompt 资源 ----
    print("\n== 3. 创建资源 ==")
    res_tool = s.post(f"{BASE}/resources", json={
        "type": "tool", "name": "测试计算器",
        "description": "冒烟测试工具", "meta": {"category": "utility", "content": "calculator"},
    })
    check(res_tool.status_code == 200, f"create tool status={res_tool.status_code}")
    tool_id = res_tool.json()["id"]

    res_prompt = s.post(f"{BASE}/resources", json={
        "type": "prompt", "name": "客服提示词",
        "description": "冒烟提示词", "meta": {"version": "v1.0", "content": "你是专业客服助手。"},
    })
    check(res_prompt.status_code == 200, f"create prompt status={res_prompt.status_code}")
    prompt_id = res_prompt.json()["id"]

    res_skill = s.post(f"{BASE}/resources", json={
        "type": "skill", "name": "数据分析技能",
        "description": "冒烟 skill", "meta": {"version": "v1.0", "content": "你具备数据分析能力。"},
    })
    check(res_skill.status_code == 200, f"create skill status={res_skill.status_code}")
    skill_id = res_skill.json()["id"]

    # ---- 3. 列表按类型过滤（含 tool） ----
    print("\n== 4. 资源列表按类型 ==")
    r = s.get(f"{BASE}/resources", params={"type": "tool"})
    check(r.status_code == 200, f"list tool status={r.status_code}")
    tool_types = [x["type"] for x in r.json().get("resources", [])]
    check(all(t == "tool" for t in tool_types), "list /resources?type=tool 全为 tool")

    # ---- 4. 创建 Agent 并挂载 tool/skill/prompt ----
    print("\n== 5. Agent 挂载 ==")
    r = s.post(f"{BASE}/agents", json={
        "name": "冒烟 Agent", "model": "Qwen3.5-397b-a17b",
        "skill_ids": [skill_id], "tool_ids": [tool_id],
        "prompt_resource_id": prompt_id,
    })
    check(r.status_code == 200, f"create agent status={r.status_code}")
    agent = r.json()
    check(agent["skill_ids"] == [skill_id], f"agent.skill_ids={agent['skill_ids']}")
    check(agent["tool_ids"] == [tool_id], f"agent.tool_ids={agent['tool_ids']}")
    check(agent["prompt_resource_id"] == prompt_id, "agent.prompt_resource_id 已保存")

    # ---- 5. 编译 RunSpec ----
    print("\n== 6. Agent 编译 RunSpec ==")
    r = s.post(f"{BASE}/agents/{agent['id']}/compile")
    check(r.status_code == 200, f"compile status={r.status_code}")
    rs = r.json().get("runspec", {})
    check(rs.get("agent_id") == agent["id"], "runspec.agent_id 匹配")
    check(rs.get("system_prompt") == "你是专业客服助手。", f"runspec 解析 prompt 资源 -> {rs.get('system_prompt')!r}")
    check(rs.get("skills") == [skill_id], "runspec.skills 透传")
    check(rs.get("tools") == [tool_id], "runspec.tools 透传")

    # ---- 6. 资源更新/删除 ----
    print("\n== 7. 资源更新/删除 ==")
    r = s.put(f"{BASE}/resources/{tool_id}", json={"name": "测试计算器改"})
    check(r.status_code == 200 and r.json()["name"] == "测试计算器改", "更新 tool 名称")
    r = s.delete(f"{BASE}/resources/{skill_id}")
    check(r.status_code == 200, f"delete skill status={r.status_code}")

    # ---- 汇总 ----
    print("\n==== 结果 ====")
    if failed == 0:
        print("ALL SMOKE TESTS PASSED")
        return 0
    print(f"{failed} test(s) FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())