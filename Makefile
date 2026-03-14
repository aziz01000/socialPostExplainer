.PHONY: help setup install run clean docker-build docker-up docker-down phoenix

help:
	@echo "Contextual Post Explainer - Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup       Setup development environment"
	@echo "  make install     Install dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make run         Start both services"
	@echo ""
	@echo "Observability (Arize Phoenix):"
	@echo "  make phoenix     Start Phoenix UI in Docker (traces at http://localhost:6006)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build images"
	@echo "  make docker-up      Start services"
	@echo "  make docker-down    Stop services"
	@echo ""
	@echo "Cleaning:"
	@echo "  make clean       Clean cache files"

setup:
	@echo "Setting up development environment..."
	cd backend && python3 -m venv venv
	cd frontend && npm install
	cp backend/.env.example backend/.env
	@echo "Setup complete! Configure backend/.env with your OpenAI API key"

install:
	cd backend && source venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

run:
	@echo "Starting services..."
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload &
	cd frontend && npm start

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf frontend/build
	rm -rf backend/data/*

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down

# Run Arize Phoenix in Docker (avoids strawberry/pydantic conflict with system Python).
# Open http://localhost:6006 to view LLM traces. Backend sends traces when PHOENIX_ENABLED=true.
phoenix:
	docker run --rm -p 6006:6006 -p 4317:4317 -it arizephoenix/phoenix:latest

.DEFAULT_GOAL := help
