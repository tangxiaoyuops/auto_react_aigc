"""简化版前端启动脚本 - 修复登录问题"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "control-plane"))
sys.path.insert(0, str(project_root / "shared"))

# 切换到控制平面目录
os.chdir(project_root / "control-plane")

# 创建数据库和测试用户
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import engine, Base, DBUser
from app.core.security import JWTManager
from datetime import datetime

async def create_test_user():
    """创建测试用户"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables created")
    
    # 检查用户是否存在
    from sqlalchemy import select
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(DBUser).where(DBUser.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # 创建测试用户
            user = DBUser(
                email="test@example.com",
                username="testuser",
                password_hash=JWTManager.get_password_hash("password123"),
                roles=["user"],
                is_active=True,
                created_at=datetime.utcnow()
            )
            session.add(user)
            await session.commit()
            print("Test user created: test@example.com / password123")
        else:
            print("Test user already exists")

# 创建测试用户
asyncio.run(create_test_user())

# 现在启动服务
import uvicorn
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8080,
    reload=True,
    reload_dirs=[str(project_root / "control-plane")]
)
