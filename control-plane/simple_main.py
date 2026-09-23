"""简化版控制平面 - 用于快速测试"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json

app = FastAPI(title="控制平面测试版", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟数据存储
sessions_db = {}
messages_db = {}
runs_db = {}

# ===== 模型定义 =====
class UserRegister(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class CreateSession(BaseModel):
    title: Optional[str] = None
    model: str = "gpt-4o"

class SendMessage(BaseModel):
    content: str

# ===== 健康检查 =====
@app.get("/")
async def root():
    return {"service": "控制平面测试版", "version": "1.0.0", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "control-plane"}

# ===== 用户认证 =====
@app.post("/api/v1/auth/register")
async def register(user: UserRegister):
    return {
        "id": "user_001",
        "email": user.email,
        "username": user.username,
        "roles": ["user"]
    }

@app.post("/api/v1/auth/login")
async def login(user: UserLogin):
    # 简化版：返回假token
    return {
        "access_token": "fake_access_token_for_testing",
        "refresh_token": "fake_refresh_token_for_testing",
        "token_type": "bearer"
    }

# ===== 会话管理 =====
@app.get("/api/v1/sessions")
async def list_sessions():
    return {
        "sessions": list(sessions_db.values()),
        "total": len(sessions_db)
    }

@app.post("/api/v1/sessions")
async def create_session(session: CreateSession):
    session_id = f"session_{len(sessions_db) + 1}"
    session_data = {
        "id": session_id,
        "title": session.title or "新会话",
        "model": session.model,
        "status": "active",
        "created_at": "2026-08-18T12:00:00"
    }
    sessions_db[session_id] = session_data
    return session_data

@app.get("/api/v1/sessions/{session_id}")
async def get_session(session_id: str):
    if session_id in sessions_db:
        return sessions_db[session_id]
    return {"error": "Session not found"}

# ===== 消息管理 =====
@app.get("/api/v1/sessions/{session_id}/messages")
async def list_messages(session_id: str):
    messages = [m for m in messages_db.values() if m.get("session_id") == session_id]
    return {"messages": messages, "total": len(messages)}

@app.post("/api/v1/sessions/{session_id}/messages")
async def send_message(session_id: str, message: SendMessage):
    # 创建消息
    message_id = f"msg_{len(messages_db) + 1}"
    message_data = {
        "id": message_id,
        "session_id": session_id,
        "role": "user",
        "content": message.content,
        "created_at": "2026-08-18T12:00:00"
    }
    messages_db[message_id] = message_data
    
    # 创建运行
    run_id = f"run_{len(runs_db) + 1}"
    run_data = {
        "id": run_id,
        "session_id": session_id,
        "status": "running",
        "created_at": "2026-08-18T12:00:00"
    }
    runs_db[run_id] = run_data
    
    return {
        "message": message_data,
        "run": run_data
    }

# ===== 运行管理 =====
@app.get("/api/v1/runs")
async def list_runs():
    return {"runs": list(runs_db.values()), "total": len(runs_db)}

@app.get("/api/v1/runs/{run_id}")
async def get_run(run_id: str):
    if run_id in runs_db:
        return runs_db[run_id]
    return {"error": "Run not found"}

# ===== 工具管理 =====
@app.get("/api/v1/tools")
async def list_tools():
    return [
        {
            "name": "web_search",
            "display_name": "网络搜索",
            "description": "搜索互联网获取信息",
            "category": "search"
        },
        {
            "name": "calculator",
            "display_name": "计算器",
            "description": "执行数学计算",
            "category": "utility"
        }
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
