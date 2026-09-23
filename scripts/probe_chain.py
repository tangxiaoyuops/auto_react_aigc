# -*- coding: utf-8 -*-
"""验证真实 LLM 链路：控制平面 -> 认知平面(Qwen3-5-397B) -> SSE (模拟前端)"""
import asyncio, json
import httpx
from collections import Counter

A = "http://localhost:8080/api/v1"

async def main():
    async with httpx.AsyncClient(timeout=90) as c:
        lr = await c.post(f"{A}/auth/login",
                          json={"email": "test@example.com", "password": "password123"})
        tok = lr.json().get("access_token")
        h = {"Authorization": f"Bearer {tok}"}

        sr = await c.get(f"{A}/sessions", headers=h)
        j = sr.json()
        sids = j if isinstance(j, list) else (j.get("items", []) if isinstance(j, dict) else [])
        if sids:
            sid = sids[0].get("id")
        else:
            sid = (await c.post(f"{A}/sessions", json={"title": "t", "model": "qwen3-5-397b-a17b"}, headers=h)).json().get("id")
        print("session", sid)

        rr = await c.post(f"{A}/sessions/{sid}/runs", headers=h,
                          json={"content": "帮我分析最近三个月销售，找环比变化并给运营建议"})
        rj = rr.json()
        rid = rj.get("run_id")
        print("run", rid, "| status", rj.get("status"))

        types = []
        results = []
        async with c.stream("GET", f"{A}/sessions/{sid}/stream",
                            headers=h, params={"run_id": rid}) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    try:
                        ev = json.loads(line[6:])
                        types.append(ev.get("type"))
                        if ev.get("type") == "result":
                            results.append(ev.get("content", {}).get("detail", ""))
                    except Exception:
                        pass
        print("event types:", dict(Counter(types)))
        for r in results:
            print("RESULT PREVIEW:", r[:200])

asyncio.run(main())