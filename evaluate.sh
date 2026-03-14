#!/bin/bash
# Run evaluation harness

echo "📊 Running Contextual Post Explainer Evaluation"
echo "================================================"

# Check if backend is set up
if [ ! -d "backend/venv" ]; then
    echo "❌ Error: Backend virtual environment not found"
    echo "Run setup.sh first"
    exit 1
fi

# Activate backend environment
cd backend
source venv/bin/activate 2>/dev/null || true

# Run evaluation
echo ""
echo "Running evaluation on 10 test posts..."
echo ""

python -m evaluation.evaluator

echo ""
echo "================================================"
echo "✅ Evaluation complete!"
echo ""
echo "Results saved to: evaluation/results.json"
echo ""
