"""Test cases for control plane API"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "control-plane"


@pytest.mark.asyncio
async def test_list_tools():
    """Test list tools endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/tools")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]


@pytest.mark.asyncio
async def test_register_and_login():
    """Test user registration and login"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Register
        register_response = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        
        # May fail if user already exists
        if register_response.status_code == 200:
            assert "id" in register_response.json()
        
        # Login
        login_response = await ac.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        
        return data["access_token"]


@pytest.mark.asyncio
async def test_create_session():
    """Test create session endpoint"""
    # First login
    token = await test_register_and_login()
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/sessions",
            json={
                "title": "Test Session",
                "model": "gpt-4o"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "Test Session"
