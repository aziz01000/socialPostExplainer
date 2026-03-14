.PHONY: help setup install run run-backend run-frontend test evaluate clean docker-build docker-up docker-down

help:
	@echo "Contextual Post Explainer - Development Commands"
	@echo "================================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          Setup development environment"
	@echo "  make install        Install all dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make run            Start both backend and frontend"
	@echo "  make run-backend    Start backend only (http://localhost:8000)"
	@echo "  make run-frontend   Start frontend only (http://localhost:3000)"
	@echo ""
	@echo "Testing & Evaluation:"
	@echo "  make test           Run evaluation harness on 10 test posts"
	@echo "  make evaluate       Same as 'make test'"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build Docker images"
	@echo "  make docker-up      Start all services with Docker Compose"
	@echo "  make docker-down    Stop all Docker Compose services"
	@echo ""
	@echo "Cleaning:"
	@echo "  make clean          Remove cache and temp files"
	@echo "  make clean-all      Remove all generated files and venv"

setup:
	@echo "Setting up development environment..."
	bash setup.sh

install:
	@echo "Installing dependencies..."
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

run:
	@echo "Starting all services..."
	bash run.sh

run-backend:
	@echo "Starting backend server..."
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	@echo "Starting frontend server..."
	cd frontend && REACT_APP_API_BASE_URL=http://localhost:8000 npm start

test: evaluate

evaluate:
	@echo "Running evaluation harness..."
	bash evaluate.sh

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf frontend/build
	rm -rf backend/data/faiss_index.pkl
	rm -rf traces.json evaluation/results.json

clean-all: clean
	rm -rf backend/venv
	rm -rf frontend/node_modules
	rm -rf backend/.env

docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker Compose services..."
	docker-compose up --build

docker-down:
	@echo "Stopping Docker Compose services..."
	docker-compose down

.DEFAULT_GOAL := help
