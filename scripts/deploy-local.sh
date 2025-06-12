#!/bin/bash

# AI Agent Startup Script
echo "Starting AI Agent..."
echo "Working directory: $(pwd)"

# Check virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "⚠ Virtual environment not found at venv/bin/activate"
fi

# Check .env file
if [ -f ".env" ]; then
    echo "✓ Found .env file"
else
    echo "⚠ .env file not found"
fi

# Start application
echo "Starting AI Agent server..."
python ai-agent/main.py