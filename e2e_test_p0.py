"""P0 端到端测试：Agent CRUD + 发送消息 + SSE 事件流 + 历史重放"""
import asyncio
import json
import httpx

BASE = "http://localhost:8080/api/v1"
EMAIL = "e2e_test@example.com"
USERNAME = "e2etest"
PASSWORD = "e2epass123"

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = ""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} {detail}")


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        # ---------- 1. 注册/登录 ----------
        print("== 1. 认证 ==")
        r = await client.post(f"{BASE}/auth/register", json={
            "email": EMAIL, "username": USERNAME, "password": PASSWORD,
        })
        if r.status_code not in (200, 400, 409):
            print(f"register unexpected: {r.status_code} {r.text}")
        r = await client.post(f"{BASE}/auth/login", json={
            "email": EMAIL, "password": PASSWORD,
        })
        check("登录", r.status_code == 200, f"status={r.status_code} {r.text}")
        token = r.json().get("access_token", "")
        headers = {"Authorization": f"Bearer {token}"}
        check("拿到 token", bool(token))

        # ---------- 2. Agent CRUD ----------
        print("== 2. Agent CRUD ==")
        r = await client.post(f"{BASE}/agents", headers=headers, json={
            "name": "销售分析助手",
            "description": "分析销售数据的智能助手",
            "model": "Qwen3.5-397b-a17b",
            "system_prompt": "你是数据分析专家，帮助用户分析销售数据。",
            "temperature": 0.5,
        })
        check("创建 Agent", r.status_code == 200, f"status={r.status_code} {r.text}")
        agent = r.json()
        agent_id = agent.get("id", "")
        check("Agent 返回 id", bool(agent_id))
        check("Agent 初始状态 draft", agent.get("status") == "draft", agent.get("status", ""))

        # 列表
        r = await client.get(f"{BASE}/agents", headers=headers)
        check("Agent 列表", r.status_code == 200 and len(r.json().get("agents", [])) >= 1)

        # stats
        r = await client.get(f"{BASE}/agents/stats", headers=headers)
        check("Agent 统计", r.status_code == 200 and r.json().get("total", 0) >= 1, r.text)

        # 更新
        r = await client.put(f"{BASE}/agents/{agent_id}", headers=headers, json={
            "system_prompt": "更新后的系统提示词",
            "temperature": 0.3,
        })
        check("更新 Agent", r.status_code == 200 and r.json().get("temperature") == 0.3)

        # 能力挂载
        r = await client.post(f"{BASE}/agents/{agent_id}/capabilities", headers=headers, json={
            "resource_type": "knowledge",
            "resource_ids": ["res-1", "res-2"],
        })
        check("挂载知识库能力",
              r.status_code == 200 and len(r.json().get("knowledge_ids", [])) == 2, r.text)

        # 上架
        r = await client.post(f"{BASE}/agents/{agent_id}/publish", headers=headers)
        check("上架 Agent", r.status_code == 200 and r.json().get("status") == "published", r.text)
        check("上架后版本号>1", r.json().get("version", 0) >= 2, f"version={r.json().get('version')}")

        # 非法状态流转: 已上架不能再上架
        r = await client.post(f"{BASE}/agents/{agent_id}/publish", headers=headers)
        check("重复上架被拒绝", r.status_code == 400, f"status={r.status_code}")

        # 下架
        r = await client.post(f"{BASE}/agents/{agent_id}/unpublish", headers=headers)
        check("下架 Agent", r.status_code == 200 and r.json().get("status") == "draft", r.text)

        # 删除
        r = await client.delete(f"{BASE}/agents/{agent_id}", headers=headers)
        check("删除 Agent", r.status_code == 200, r.text)

        # ---------- 3. 会话 + 发送消息 + SSE ----------
        print("== 3. Session / Run / SSE ==")
        r = await client.post(f"{BASE}/sessions", headers=headers, json={
            "title": "调试会话",
            "model": "Qwen3.5-397b-a17b",
        })
        check("创建会话", r.status_code == 200, r.text)
        session_id = r.json().get("id", "")
        check("会话返回 id", bool(session_id))

        # 发送消息 -> run
        r = await client.post(f"{BASE}/sessions/{session_id}/runs", headers=headers, json={
            "content": "帮我分析一下最近的销售数据",
            "agent": {"id": agent_id, "name": "销售分析助手"},
        })
        check("发送消息启动 Run", r.status_code == 200, f"status={r.status_code} {r.text}")
        run_id = r.json().get("run_id", "")
        check("Run 返回 run_id", bool(run_id))

        # 轮询等待 run 完成
        print("  ...等待 Run 执行...")
        status = ""
        for _ in range(40):
            await asyncio.sleep(1)
            r = await client.get(f"{BASE}/runs/{run_id}", headers=headers)
            if r.status_code == 200:
                status = r.json().get("status", "")
                if status in ("completed", "failed", "cancelled"):
                    break
        check("Run 最终状态", status == "completed", f"status={status}")
        if status == "failed":
            print(f"    run error: {r.text}")

        # 历史事件重放
        r = await client.get(f"{BASE}/sessions/{session_id}/runs/{run_id}/events", headers=headers)
        check("获取 Run 事件历史", r.status_code == 200, r.text)
        events = r.json().get("events", [])
        check("事件数 >= 4 (start/thought/tool/result/end)",
              len(events) >= 4, f"count={len(events)}")
        if events:
            print(f"    事件类型序列: {[e['type'] for e in events]}")

        # ---------- 4. Resource 管理 ----------
        print("== 4. Resource CRUD ==")

        # 内置能力池
        r = await client.get(f"{BASE}/resources/pool", headers=headers)
        check("能力池", r.status_code == 200 and len(r.json().get("knowledge", [])) == 3, r.text)

        # 创建 5 类资源
        created_ids = {}
        for rt in ("kb", "skill", "prompt", "ontology", "ds"):
            r = await client.post(f"{BASE}/resources", headers=headers, json={
                "type": rt,
                "name": f"测试{rt}资源",
                "description": f"{rt} 描述",
                "meta": {"version": "v1", "doc_count": 10},
            })
            check(f"创建 {rt} 资源", r.status_code == 200, f"status={r.status_code} {r.text}")
            created_ids[rt] = r.json().get("id", "")

        # 非法类型被拒
        r = await client.post(f"{BASE}/resources", headers=headers, json={
            "type": "badtype", "name": "x",
        })
        check("非法资源类型返回 400", r.status_code == 400, f"status={r.status_code}")

        # 按类型筛选
        r = await client.get(f"{BASE}/resources?type=kb", headers=headers)
        kb_list = r.json().get("resources", [])
        check("按 kb 类型筛选",
              r.status_code == 200 and all(x["type"] == "kb" for x in kb_list) and len(kb_list) >= 1,
              r.text)

        # 搜索
        r = await client.get(f"{BASE}/resources?keyword=测试skill", headers=headers)
        check("按关键字搜索",
              r.status_code == 200 and any("skill" in x["name"] for x in r.json().get("resources", [])),
              r.text)

        # 更新
        r = await client.put(f"{BASE}/resources/{created_ids['kb']}", headers=headers, json={
            "description": "更新后的知识库描述",
        })
        check("更新资源", r.status_code == 200 and r.json().get("description") == "更新后的知识库描述", r.text)

        # 单查
        r = await client.get(f"{BASE}/resources/{created_ids['skill']}", headers=headers)
        check("获取单个资源", r.status_code == 200 and r.json().get("type") == "skill", r.text)

        # 删除
        r = await client.delete(f"{BASE}/resources/{created_ids['kb']}", headers=headers)
        check("删除资源", r.status_code == 200, r.text)
        r = await client.get(f"{BASE}/resources/{created_ids['kb']}", headers=headers)
        check("删除后查不到", r.status_code == 404, f"status={r.status_code}")

        # ---------- 5. Space / 成员管理 ----------
        print("== 5. Space / Members ==")

        r = await client.post(f"{BASE}/spaces", headers=headers, json={
            "name": "测试领域空间",
            "description": "用于端到端测试",
        })
        check("创建空间", r.status_code == 200, f"status={r.status_code} {r.text}")
        space_id = r.json().get("id", "")
        check("空间返回 id", bool(space_id))

        # 创建者自动成为 admin（通过成员列表验证）
        r = await client.get(f"{BASE}/spaces/{space_id}/members", headers=headers)
        owner_member = next(
            (m for m in r.json().get("members", []) if m.get("account") == EMAIL), None
        )
        check("创建者自动成为 admin", owner_member is not None and owner_member.get("role") == "admin",
              f"members={r.json().get('members')}")

        # 我的空间
        r = await client.get(f"{BASE}/spaces/me", headers=headers)
        check("我的空间列表", r.status_code == 200 and any(
            s["id"] == space_id for s in r.json().get("spaces", [])
        ), r.text)

        # 邀请成员
        r = await client.post(f"{BASE}/spaces/{space_id}/members/invite", headers=headers, json={
            "account": "invitee@example.com",
            "role": "member",
        })
        check("邀请成员", r.status_code == 200, f"status={r.status_code} {r.text}")
        member_id = r.json().get("id", "")

        # 成员列表
        r = await client.get(f"{BASE}/spaces/{space_id}/members", headers=headers)
        check("成员列表", r.status_code == 200 and r.json().get("total", 0) >= 2, r.text)

        # 停用成员
        r = await client.put(f"{BASE}/spaces/{space_id}/members/{member_id}", headers=headers, json={
            "status": "disabled",
        })
        check("停用成员", r.status_code == 200 and r.json().get("status") == "disabled", r.text)

        # 改角色
        r = await client.put(f"{BASE}/spaces/{space_id}/members/{member_id}", headers=headers, json={
            "role": "admin",
        })
        check("改成员角色", r.status_code == 200 and r.json().get("role") == "admin", r.text)

        # 非法角色被忽略（保持原值）
        r = await client.put(f"{BASE}/spaces/{space_id}/members/{member_id}", headers=headers, json={
            "role": "superuser",
        })
        check("非法角色被忽略", r.status_code == 200 and r.json().get("role") == "admin", r.text)

        # ---------- 6. Evaluation ----------
        print("== 6. Evaluation ==")

        # 创建评测集
        r = await client.post(f"{BASE}/evaluations/datasets", headers=headers, json={
            "name": "回归评测集",
            "description": "客服助手回归",
        })
        check("创建评测集", r.status_code == 200, f"status={r.status_code} {r.text}")
        dataset_id = r.json().get("id", "")

        # 添加用例
        for i, q in enumerate(["北京社保基数", "公积金提取材料", "个税扣除项目", "报销流程", "请假制度"]):
            r = await client.post(f"{BASE}/evaluations/datasets/{dataset_id}/cases", headers=headers, json={
                "question": q,
                "expected": f"关于{q}的标准答案",
            })
            if r.status_code != 200:
                break
        r = await client.get(f"{BASE}/evaluations/datasets/{dataset_id}/cases", headers=headers)
        check("添加 5 个用例", r.status_code == 200 and r.json().get("total") == 5, r.text)

        # 评测集列表（case_count 反映）
        r = await client.get(f"{BASE}/evaluations/datasets", headers=headers)
        ds = next((d for d in r.json().get("datasets", []) if d["id"] == dataset_id), None)
        check("评测集 case_count 更新", ds is not None and ds["case_count"] == 5, str(ds))

        # 创建评测任务
        r = await client.post(f"{BASE}/evaluations/tasks", headers=headers, json={
            "name": "回归评测任务",
            "agent_id": "agent_x",
            "agent_name": "客服助手",
            "dataset_id": dataset_id,
        })
        check("创建评测任务", r.status_code == 200, f"status={r.status_code} {r.text}")
        task_id = r.json().get("id", "")
        check("任务初始 pending", r.json().get("status") == "pending", r.json().get("status", ""))

        # 轮询等待任务完成
        print("  ...等待评测任务执行...")
        for _ in range(30):
            await asyncio.sleep(0.5)
            r = await client.get(f"{BASE}/evaluations/tasks", headers=headers)
            task = next((t for t in r.json().get("tasks", []) if t["id"] == task_id), None)
            if task and task["status"] in ("completed", "failed"):
                break
        check("评测任务完成", task is not None and task["status"] == "completed", str(task))
        check("任务 progress=100", task and task["progress"] == 100, str(task and task.get("progress")))

        # 报告
        r = await client.get(f"{BASE}/evaluations/tasks/{task_id}/report", headers=headers)
        report = r.json()
        check("获取评测报告", r.status_code == 200, r.text)
        check("报告含用例明细", len(report.get("cases", [])) == 5, f"cases={len(report.get('cases', []))}")
        check("报告含通过率", "pass_rate" in report, report.get("pass_rate", ""))

        # 删除评测集
        r = await client.delete(f"{BASE}/evaluations/datasets/{dataset_id}", headers=headers)
        check("删除评测集", r.status_code == 200, r.text)

        # ---------- 汇总 ----------
        print(f"\n===== 结果: {passed} passed, {failed} failed =====")
        if failed > 0:
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())