#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Start the server
echo "🎵 Starting LLM2Fx App..."
echo "📱 Frontend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🏥 Health: http://localhost:8000/healthz"
echo ""
echo "Press Ctrl+C to stop"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
