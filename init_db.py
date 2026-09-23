"""初始化数据库和创建测试用户"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import sys
from pathlib import Path
import os

# 切换到控制平面目录
os.chdir(Path(__file__).parent / "control-plane")

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "control-plane"))
sys.path.insert(0, str(Path(__file__).parent / "shared"))

from app.db.database import engine, Base, DBUser
from app.core.security import JWTManager
from datetime import datetime

async def init_database():
    """初始化数据库"""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")
    
    # 创建测试用户
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(DBUser).where(DBUser.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
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
            
        # 创建管理员用户
        result = await session.execute(
            select(DBUser).where(DBUser.email == "admin@agent-platform.com")
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            admin = DBUser(
                email="admin@agent-platform.com",
                username="admin",
                password_hash=JWTManager.get_password_hash("admin123"),
                roles=["admin", "user"],
                is_active=True,
                created_at=datetime.utcnow()
            )
            session.add(admin)
            await session.commit()
            print("Admin user created: admin@agent-platform.com / admin123")

if __name__ == "__main__":
    asyncio.run(init_database())
