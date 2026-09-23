"""为 test 用户创建示例 Agent（通过真实 API，保证数据一致）"""
import asyncio
import httpx

EMAIL = "test@example.com"
PASSWORD = "password123"
BASE = "http://localhost:8080/api/v1"

SEED_AGENTS = [
    {
        "name": "客服助手",
        "description": "面向客户的服务型Agent，结合知识库回答业务问题",
        "model": "Qwen3.5-397b-a17b",
        "system_prompt": "你是一名专业的智能客服助手。请基于知识库中的业务信息，耐心、准确地回答用户的问题。",
        "knowledge_ids": [],
        "ontology_ids": [],
        "skill_ids": [],
    },
    {
        "name": "LegalRegulatoryDashboard_1",
        "description": "法规监管数据分析Agent",
        "model": "Qwen3.5-397b-a17b",
        "system_prompt": "你是法规监管数据分析助手，负责检索并解读最新监管法规，并结合业务数据给出合规建议。",
        "knowledge_ids": [],
        "ontology_ids": [],
        "skill_ids": [],
    },
    {
        "name": "智能研报Agent",
        "description": "自动生成行业研究报告的Agent",
        "model": "claude-3-5-sonnet",
        "system_prompt": "你是行业研究助手，负责收集信息、分析趋势并生成研究报告。",
        "knowledge_ids": [],
        "ontology_ids": [],
        "skill_ids": [],
    },
]


async def main():
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
        if r.status_code != 200:
            print("login failed", r.text)
            return
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        for ag in SEED_AGENTS:
            r = await c.post(f"{BASE}/agents", headers=headers, json=ag)
            if r.status_code == 200:
                print("created:", ag["name"], "->", r.json()["id"][:8])
            else:
                print("failed:", ag["name"], r.status_code, r.text)


if __name__ == "__main__":
    asyncio.run(main())