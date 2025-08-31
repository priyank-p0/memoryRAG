#!/bin/bash

# Multi-Model Chat Interface Setup Script

echo "🚀 Setting up Multi-Model Chat Interface..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed. Please install Node.js 16 or higher."
    exit 1
fi

echo "✅ Python and Node.js found"

# Setup backend
echo "📦 Setting up Python backend..."
cd backend

# Create virtual environment with Python 3.12 for better compatibility
if command -v python3.12 &> /dev/null; then
    echo "✅ Using Python 3.12 for better compatibility"
    python3.12 -m venv venv
elif command -v python3.11 &> /dev/null; then
    echo "✅ Using Python 3.11"
    python3.11 -m venv venv
else
    echo "⚠️  Using default Python 3"
    python3 -m venv venv
fi

source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Create .env file from template
if [ ! -f .env ]; then
    cp env_example.txt .env
    echo "📝 Created .env file. Please edit it with your API keys."
else
    echo "⚠️  .env file already exists"
fi

cd ..

# Setup frontend
echo "📦 Setting up React frontend..."
npm install --legacy-peer-deps

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit backend/.env with your API keys"
echo "2. Start the backend: cd backend && python run_server.py"
echo "3. Start the frontend: npm run dev"
echo ""
echo "🌐 The app will be available at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
