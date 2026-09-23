"""Database configuration"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, JSON, Enum as SQLEnum
from datetime import datetime
import uuid

from app.core.config import settings

# Create async engine
# SQLite doesn't support pool_size
if "sqlite" in settings.DATABASE_URL:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW
    )

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


# Database Models
class DBSession(Base):
    """Session database model"""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    title = Column(String(255))
    model = Column(String(100), default="gpt-4o")
    tools = Column(JSON, default=list)
    skills = Column(JSON, default=list)
    system_prompt = Column(String)
    status = Column(String(50), default="active", index=True)
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class DBMessage(Base):
    """Message database model"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(String, nullable=False)
    model = Column(String(100))
    tokens_used = Column(Integer)
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class DBRun(Base):
    """Run database model"""
    __tablename__ = "runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    status = Column(String(50), default="pending", index=True)
    model = Column(String(100))
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    tool_calls_count = Column(Integer, default=0)
    reasoning_steps = Column(Integer, default=0)
    error_message = Column(String)
    extra_data = Column(JSON, default=dict)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class DBRunEvent(Base):
    """Run event database model"""
    __tablename__ = "run_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    content = Column(JSON, nullable=False)
    sequence = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DBUser(Base):
    """User database model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    roles = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# ======================= P0: Agent 服务 =======================

class DBAgent(Base):
    """Agent 配置模型（前端 Agent 配置页 / 列表页）"""
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    space_id = Column(String, index=True)          # 所属空间
    name = Column(String(255), nullable=False)     # Agent 名称
    description = Column(String)
    model = Column(String(100), default="Qwen3.5-397b-a17b")
    system_prompt = Column(String)
    avatar_color = Column(String(20), default="#1677ff")
    status = Column(String(50), default="draft", index=True)  # draft/published/archived
    version = Column(Integer, default=1)

    # 运行时配置（对应前端配置表单）
    temperature = Column(Float, default=0.7)
    max_iterations = Column(Integer, default=10)
    timeout = Column(Integer, default=300)
    greeting = Column(String)
    suggestion_questions = Column(JSON, default=list)

    # 能力关联: 知识库/本体/Skill (resource id 数组)
    knowledge_ids = Column(JSON, default=list)
    ontology_ids = Column(JSON, default=list)
    skill_ids = Column(JSON, default=list)

    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class DBAgentVersion(Base):
    """Agent 版本历史（发布时打快照）"""
    __tablename__ = "agent_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False)   # 发布时整条 Agent 配置快照
    status = Column(String(50), default="published")
    published_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


# ======================= P1: Resource 服务 =======================

class DBResource(Base):
    """资源池：知识库/本体/Skill/提示词/数据源 统一表

    对应前端 resources/index.tsx 的 5 个 Tab（kb/skill/prompt/ontology/ds）
    """
    __tablename__ = "resources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)  # kb/skill/prompt/ontology/ds
    name = Column(String(255), nullable=False)
    description = Column(String)
    meta = Column(JSON, default=dict)   # 版本号/文档数/接入状态等
    origin = Column(String(50), default="custom")  # custom/seed（区分内置池与自建）
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# ======================= P1: Space 服务 =======================

class DBSpace(Base):
    """领域空间"""
    __tablename__ = "spaces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(String)
    owner_id = Column(String, nullable=False, index=True)
    status = Column(String(20), default="active")  # active/disabled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class DBSpaceMember(Base):
    """空间成员"""
    __tablename__ = "space_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    space_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String(100))            # 展示名
    account = Column(String(255))       # 邮箱/账号
    role = Column(String(50), default="member")  # admin/member
    status = Column(String(20), default="active")  # active/disabled
    joined_at = Column(DateTime, default=datetime.utcnow)


# ======================= P1: Evaluation 服务 =======================

class DBEvalDataset(Base):
    """评测数据集"""
    __tablename__ = "eval_datasets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String)
    case_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class DBEvalCase(Base):
    """评测用例"""
    __tablename__ = "eval_cases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, nullable=False, index=True)
    question = Column(String, nullable=False)
    expected = Column(String)
    actual = Column(String)
    score = Column(Float, default=0.0)
    status = Column(String(20), default="passed")  # passed/failed
    created_at = Column(DateTime, default=datetime.utcnow)


class DBEvalTask(Base):
    """评测任务"""
    __tablename__ = "eval_tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    agent_id = Column(String)
    agent_name = Column(String)
    dataset_id = Column(String, index=True)
    status = Column(String(20), default="pending", index=True)  # pending/running/completed/failed
    progress = Column(Integer, default=0)
    total_cases = Column(Integer, default=0)
    passed_cases = Column(Integer, default=0)
    report = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


async def init_db():
    """Initialize database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session
