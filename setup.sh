#!/bin/bash
# Setup scriptfor development environment

echo "🚀 Setting up Contextual Post Explainer"
echo "========================================"

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python version: $python_version"

# Create backend environment
echo ""
echo "✓ Setting up backend environment..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Created virtual environment"
fi

source venv/bin/activate

pip install -r requirements.txt --quiet
echo "  Installed Python dependencies"

# Create .env file
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created .env file (configure with your OpenAI API key)"
else
    echo "  .env already exists"
fi

# Create data directory
mkdir -p data
echo "  Created data directory"

cd ..

# Setup frontend
echo ""
echo "✓ Setting up frontend environment..."
cd frontend

if [ ! -d "node_modules" ]; then
    npm install --silent
    echo "  Installed npm dependencies"
else
    echo "  npm dependencies already installed"
fi

cd ..

echo ""
echo "========================================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your OpenAI API key in backend/.env"
echo "2. Start backend:   cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "3. Start frontend:  cd frontend && REACT_APP_API_BASE_URL=http://localhost:8000 npm start"
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "Or use Docker:"
echo "  docker-compose up --build"
