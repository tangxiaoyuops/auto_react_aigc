"""Health check routes"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cognition-plane",
        "version": "1.0.0"
    }
