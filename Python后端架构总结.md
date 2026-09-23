# 自主规划平台 - Python后端架构总结

**更新日期**: 2026-08-18
**架构类型**: 统一Python技术栈

---

## 一、架构优势

### 1.1 统一技术栈的好处

| 优势 | 说明 |
|------|------|
| **代码复用** | 控制平面和认知平面可以共享模型、工具类、配置等 |
| **团队效率** | 团队只需掌握一种语言，降低学习成本和沟通成本 |
| **部署简化** | 统一的容器镜像、依赖管理、CI/CD流程 |
| **调试便捷** | 统一的日志格式、错误处理、监控方案 |
| **AI生态优势** | Python拥有最完善的AI/ML生态，便于集成最新技术 |

### 1.2 与Go方案对比

| 维度 | Go方案 | Python方案 | 结论 |
|------|--------|-----------|------|
| 性能 | 更高(原生编译) | 足够高(异步IO) | Python性能足以应对网关场景 |
| 并发 | Goroutine轻量 | asyncio + uvicorn | Python异步方案成熟 |
| 内存占用 | 更低 | 较高 | 可通过容器化优化 |
| 开发效率 | 中等 | 更高 | Python开发速度快 |
| 生态 | 系统编程强 | AI/ML极强 | Python更适合AI平台 |
| 运维复杂度 | 低 | 中等 | 差异不大 |

**核心观点**: 对于AI平台，Python的生态优势远大于Go的性能优势。

---

## 二、服务架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Python统一后端架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              控制平面 (Control Plane)                     │   │
│  │  FastAPI + SQLAlchemy + Redis + JWT                     │   │
│  │  端口: 8080                                              │   │
│  │  职责: 会话管理、认证鉴权、事件持久化、SSE推送            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           │ HTTP/gRPC                           │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              认知平面 (Cognition Plane)                   │   │
│  │  FastAPI + LangGraph + LangChain + MCP                  │   │
│  │  端口: 8000                                              │   │
│  │  职责: Agent推理、工具调用、技能执行                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 共享代码层

```
shared/
├── __init__.py
├── models/              # 共享数据模型
│   ├── session.py
│   ├── message.py
│   ├── run.py
│   └── event.py
├── schemas/             # Pydantic schemas
│   ├── requests.py
│   └── responses.py
├── utils/               # 工具函数
│   ├── logging.py
│   ├── redis.py
│   └── database.py
└── config.py            # 共享配置
```

---

## 三、控制平面实现

### 3.1 核心技术栈

```python
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.0
alembic==1.13.0
asyncpg==0.29.0           # PostgreSQL异步驱动
redis==5.0.0              # Redis客户端
pyjwt==2.8.0              # JWT认证
passlib[bcrypt]==1.7.4    # 密码哈希
python-multipart==0.0.9   # 文件上传
httpx==0.27.0             # 异步HTTP客户端
pydantic==2.7.0
pydantic-settings==2.2.0
```

### 3.2 应用入口

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import sessions, messages, runs, tools, auth
from core.config import settings
from db.database import init_db

app = FastAPI(
    title="Agent Platform - Control Plane",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.auth_router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["Messages"])
app.include_router(runs.router, prefix="/api/v1/runs", tags=["Runs"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["Tools"])

@app.on_event("startup")
async def startup():
    await init_db()
    # 初始化Redis连接池
    # 初始化SSE管理器

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "control-plane"}
```

### 3.3 数据库配置

```python
# db/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

---

## 四、认知平面实现

### 4.1 核心技术栈

```python
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
langgraph==0.2.0
langchain==0.3.0
langchain-openai==0.2.0
langchain-anthropic==0.2.0
mcp==0.9.0                # MCP协议
pydantic==2.7.0
redis==5.0.0
sqlalchemy==2.0.0
asyncpg==0.29.0
```

### 4.2 Agent执行接口

```python
# api/routes/agent.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from services.agent_service import AgentService

router = APIRouter()

@router.post("/execute")
async def execute_agent(
    request: AgentExecuteRequest,
    agent_service: AgentService = Depends()
):
    """执行Agent（同步）"""
    result = await agent_service.execute(request)
    return result

@router.post("/execute/stream")
async def execute_agent_stream(
    request: AgentExecuteRequest,
    agent_service: AgentService = Depends()
):
    """执行Agent（流式）"""
    return StreamingResponse(
        agent_service.execute_stream(request),
        media_type="text/event-stream"
    )
```

---

## 五、服务间通信

### 5.1 HTTP通信

```python
# control-plane调用cognition-plane
import httpx
from core.config import settings

class CognitionClient:
    def __init__(self):
        self.base_url = settings.COGNITION_URL
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def execute_agent_stream(self, request: dict):
        """流式调用Agent"""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/v1/agent/execute/stream",
            json=request
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield line
    
    async def close(self):
        await self.client.aclose()
```

### 5.2 共享Redis事件流

```python
# 控制平面写入事件流
await redis.xadd(
    f"stream:{run_id}",
    {
        "event_type": event_type,
        "content": json.dumps(content)
    }
)

# 前端通过控制平面SSE读取
# 认知平面也写入同一流，实现事件合并
```

---

## 六、部署架构

### 6.1 Docker Compose

```yaml
services:
  control-plane:
    build: ./control-plane
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql+asyncpg://...
      - REDIS_URL=redis://redis:6379
      - COGNITION_URL=http://cognition-plane:8000
    depends_on:
      - postgres
      - redis
  
  cognition-plane:
    build: ./cognition-plane
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://...
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
```

### 6.2 Kubernetes

两个服务都是Python应用，部署方式相同：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: control-plane
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: control-plane
        image: agent-platform/control-plane:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## 七、性能优化

### 7.1 异步编程最佳实践

```python
# 1. 使用asyncio并发
async def execute_multiple_tools(tool_calls: List[ToolCall]):
    tasks = [execute_tool(call) for call in tool_calls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# 2. 数据库连接池
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

# 3. Redis连接池
redis = Redis(
    connection_pool=ConnectionPool(
        max_connections=50,
        decode_responses=True
    )
)

# 4. HTTP连接池
http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=100),
    timeout=300.0
)
```

### 7.2 缓存策略

```python
# 会话缓存
session_cache_ttl = 3600  # 1小时

# 工具列表缓存
tools_list_cache_ttl = 300  # 5分钟

# 用户权限缓存
user_permissions_ttl = 600  # 10分钟

# 使用Redis缓存
async def get_session_with_cache(session_id: str) -> Session:
    # 先查缓存
    cached = await redis.get(f"session:{session_id}")
    if cached:
        return Session.parse_raw(cached)
    
    # 查数据库
    session = await session_repo.get(session_id)
    if session:
        await redis.setex(
            f"session:{session_id}",
            session_cache_ttl,
            session.json()
        )
    
    return session
```

---

## 八、开发工具链

### 8.1 项目结构

```
agent-platform/
├── control-plane/          # 控制平面
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
│
├── cognition-plane/        # 认知平面
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── shared/                 # 共享代码
│   ├── models/
│   ├── schemas/
│   └── utils/
│
├── frontend/               # 前端
│   ├── src/
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

### 8.2 开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --port 8080

# 运行测试
pytest tests/ -v --cov=app

# 代码格式化
black app/
isort app/

# 类型检查
mypy app/
```

---

## 九、总结

### 9.1 架构决策记录

**决策**: 控制平面使用Python而非Go

**原因**:
1. 统一技术栈，降低维护成本
2. Python AI生态完善，便于集成
3. FastAPI性能足够应对网关场景
4. 团队Python经验丰富

**权衡**:
- 放弃了Go的高性能和低内存占用
- 获得了更好的开发效率和生态支持
- 性能可通过异步IO和容器化优化

### 9.2 关键技术点

| 技术点 | 实现方案 |
|--------|---------|
| Web框架 | FastAPI (高性能异步) |
| ORM | SQLAlchemy 2.0 (异步支持) |
| 认证 | JWT + Passlib |
| 缓存 | Redis (连接池) |
| 数据库 | PostgreSQL + asyncpg |
| 流式响应 | SSE (Server-Sent Events) |
| 服务通信 | HTTP + Redis Stream |
| Agent引擎 | LangGraph + LangChain |

### 9.3 下一步计划

1. **MVP开发** (第1-2个月)
   - 实现控制平面核心功能
   - 实现认知平面Agent引擎
   - 前端基础界面

2. **功能完善** (第3-4个月)
   - 工具系统
   - 技能系统
   - 监控告警

3. **生产部署** (第5-6个月)
   - Kubernetes部署
   - 性能优化
   - 安全加固

---

**文档版本**: v1.0  
**最后更新**: 2026-08-18
