#!/bin/bash

# Start development environment

set -e

echo "🚀 Starting Agent Platform..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

# Start infrastructure
echo "📦 Starting infrastructure services..."
docker-compose up -d postgres redis

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 5

# Start control plane
echo "🔧 Starting control plane..."
cd control-plane
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
pip install -r requirements.txt
alembic upgrade head 2>/dev/null || echo "Database migration skipped"
uvicorn app.main:app --reload --port 8080 &
CONTROL_PID=$!
cd ..

# Start cognition plane
echo "🧠 Starting cognition plane..."
cd cognition-plane
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000 &
COGNITION_PID=$!
cd ..

echo ""
echo "✅ Agent Platform is running!"
echo ""
echo "📊 Services:"
echo "  - Control Plane: http://localhost:8080"
echo "  - Control Plane Docs: http://localhost:8080/docs"
echo "  - Cognition Plane: http://localhost:8000"
echo "  - Cognition Plane Docs: http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Wait for interrupt
trap "echo ''; echo '🛑 Stopping services...'; kill $CONTROL_PID $COGNITION_PID; docker-compose down; exit 0" INT TERM

wait
