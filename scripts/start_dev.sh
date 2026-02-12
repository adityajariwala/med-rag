#!/bin/bash

# Development startup script for Med-RAG
# This script starts both the FastAPI backend and Streamlit frontend

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏥 Starting Med-RAG Development Environment${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found!${NC}"
    echo "Copy .env.example to .env and fill in your API keys:"
    echo "  cp .env.example .env"
    echo ""
    exit 1
fi

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ] && [ -z "$PYENV_VERSION" ]; then
    echo -e "${YELLOW}⚠️  Warning: No virtual environment detected!${NC}"
    echo "Activate your virtual environment first:"
    echo "  pyenv local med-rag"
    echo "  OR"
    echo "  source .venv/bin/activate"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Environment checks passed${NC}"
echo ""

# Start FastAPI in background
echo -e "${GREEN}🚀 Starting FastAPI backend...${NC}"
uvicorn src.api:app --reload --port 8000 &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API to start..."
sleep 3

# Check if API is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${YELLOW}⚠️  API may not be ready yet. Check the logs above.${NC}"
fi

echo ""
echo -e "${GREEN}🎨 Starting Streamlit frontend...${NC}"
streamlit run src/app.py --server.port 8501 &
STREAMLIT_PID=$!

echo ""
echo -e "${GREEN}✅ Med-RAG is running!${NC}"
echo ""
echo "📍 Access points:"
echo "   - Streamlit UI:    http://localhost:8501"
echo "   - FastAPI docs:    http://localhost:8000/docs"
echo "   - API health:      http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for user interrupt
trap "echo ''; echo 'Stopping services...'; kill $API_PID $STREAMLIT_PID 2>/dev/null; exit 0" INT

# Keep script running
wait
