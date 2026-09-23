"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db
from app.api.routes import sessions, messages, runs, auth, tools, agents, resources, spaces, evaluations
from app.services.sse_manager import SSEManager

# Global instances
redis_client = None
sse_manager = None


class MockRedis:
    """Mock Redis client for development"""
    async def get(self, key):
        return None
    
    async def setex(self, key, ttl, value):
        pass
    
    async def delete(self, *keys):
        pass
    
    async def incr(self, key):
        return 1
    
    async def xadd(self, stream, fields):
        pass
    
    async def close(self):
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    global redis_client, sse_manager
    
    # Startup
    print("Initializing database...")
    await init_db()
    print("Database initialized")
    
    # Initialize Redis (or Mock) —— from_url 是惰性连接，需 ping 验证
    try:
        import redis.asyncio as redis
        candidate = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await candidate.ping()
        redis_client = candidate
        print("Redis connected")
    except Exception as e:
        print(f"Redis not available, using mock: {e}")
        if 'candidate' in locals():
            await candidate.close()
        redis_client = MockRedis()
    
    # Initialize SSE Manager
    sse_manager = SSEManager()

    # Store in app state
    app.state.redis = redis_client
    app.state.sse_manager = sse_manager
    app.state.event_recorder = None  # 按需创建（见 sessions.py get_run_events）
    
    yield
    
    # Shutdown
    if redis_client:
        await redis_client.close()
    print("Application shutdown")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(messages.router, prefix="/api/v1", tags=["Messages"])
app.include_router(runs.router, prefix="/api/v1/runs", tags=["Runs"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["Tools"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(resources.router, prefix="/api/v1/resources", tags=["Resources"])
app.include_router(spaces.router, prefix="/api/v1/spaces", tags=["Spaces"])
app.include_router(evaluations.router, prefix="/api/v1/evaluations", tags=["Evaluations"])


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "control-plane",
        "version": settings.VERSION
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs" if settings.DEBUG else "disabled"
    }
