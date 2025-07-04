#!/bin/bash

# Complex RAG System Setup Script
# This script helps set up the ColPali RAG system for automotive industry PDFs

set -e

echo "🚗 Complex RAG System Setup for Automotive Industry"
echo "=================================================="

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.13"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version is compatible"
else
    echo "❌ Python $python_version is too old. Please install Python 3.13+"
    exit 1
fi

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "✅ uv is available"
    USE_UV=true
else
    echo "⚠️  uv not found, using pip"
    USE_UV=false
fi

# Install dependencies
echo "📦 Installing dependencies..."
if [ "$USE_UV" = true ]; then
    uv sync
else
    pip install -e .
fi

# Check if Docker is available for Qdrant
if command -v docker &> /dev/null; then
    echo "✅ Docker is available"
    echo "🐳 Starting Qdrant with Docker..."
    
    # Check if Qdrant container is already running
    if docker ps | grep -q qdrant; then
        echo "✅ Qdrant is already running"
    else
        echo "🚀 Starting Qdrant container..."
        docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
        echo "⏳ Waiting for Qdrant to start..."
        sleep 5
    fi
else
    echo "⚠️  Docker not found. Please install Docker or start Qdrant manually:"
    echo "   docker run -p 6333:6333 qdrant/qdrant"
fi

# Test Qdrant connection
echo "🔍 Testing Qdrant connection..."
if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo "✅ Qdrant is accessible"
else
    echo "❌ Cannot connect to Qdrant. Please ensure it's running on localhost:6333"
    echo "   You can start it with: docker run -p 6333:6333 qdrant/qdrant"
fi

# Create cache directories
echo "📁 Creating cache directories..."
mkdir -p cache/models
mkdir -p cache/embeddings

# Test the system
echo "🧪 Testing the RAG system..."
if python test_rag.py --help > /dev/null 2>&1; then
    echo "✅ Test script is working"
else
    echo "❌ Test script failed to load"
    exit 1
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Test the system: python test_rag.py"
echo "2. Index your PDF: python main.py index your_manual.pdf"
echo "3. Search documents: python main.py search 'engine specifications'"
echo ""
echo "For more information, see README.md"
echo ""
echo "Happy searching! 🚗🔍" 