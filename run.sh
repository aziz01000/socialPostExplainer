#!/bin/bash
# Run script for development

echo "🎯 Starting Contextual Post Explainer (Development)"
echo "=================================================="

# Check if backend/.env exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env not found"
    echo "Please run: cp backend/.env.example backend/.env"
    echo "Then configure your OpenAI API key in backend/.env"
    exit 1
fi

# Start backend
echo ""
echo "Starting backend server..."
cd backend
source venv/bin/activate 2>/dev/null || true
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✓ Backend running (PID: $BACKEND_PID)"

cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend
echo ""
echo "Starting frontend server..."
cd frontend
REACT_APP_API_BASE_URL=http://localhost:8000 npm start &
FRONTEND_PID=$!
echo "✓ Frontend running (PID: $FRONTEND_PID)"

cd ..

echo ""
echo "=================================================="
echo "🎉 All services started!"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Health:   http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================================="

# Wait for both processes
wait
