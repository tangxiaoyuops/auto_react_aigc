# Start development environment for Windows

Write-Host "🚀 Starting Agent Platform..." -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Create .env file if not exists
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

# Start infrastructure
Write-Host "📦 Starting infrastructure services..." -ForegroundColor Yellow
docker-compose up -d postgres redis

# Wait for services
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "✅ Infrastructure services are ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Services:" -ForegroundColor Cyan
Write-Host "  - PostgreSQL: localhost:5432"
Write-Host "  - Redis: localhost:6379"
Write-Host ""
Write-Host "🔧 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Open a new terminal and run: cd control-plane && python -m venv venv && .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt && alembic upgrade head && uvicorn app.main:app --reload --port 8080"
Write-Host "  2. Open another terminal and run: cd cognition-plane && python -m venv venv && .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000"
Write-Host ""
Write-Host "📚 API Documentation:" -ForegroundColor Cyan
Write-Host "  - Control Plane: http://localhost:8080/docs"
Write-Host "  - Cognition Plane: http://localhost:8000/docs"
Write-Host ""
