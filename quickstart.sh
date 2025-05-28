#!/bin/bash

# News Copilot Quick Start Script

set -e

echo "🚀 News Copilot Quick Start"
echo "=========================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm"
    exit 1
fi

echo "✅ Prerequisites OK"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Python dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# API Keys
XAI_API_KEY=

# Supabase Configuration (optional for local testing)
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=

# Local Development
BASE_URL=http://localhost:8080
FLASK_PORT=8080
DEBUG_MODE=true
AUTH_REQUIRED=false
EOL
    echo "✅ .env file created"
    echo "⚠️  Please add your XAI_API_KEY to the .env file"
    echo ""
fi

# Check if XAI_API_KEY is set
if [ -f ".env" ]; then
    source .env
    if [ -z "$XAI_API_KEY" ]; then
        echo "⚠️  XAI_API_KEY is not set in .env file"
        echo "Please add your Grok API key to continue"
        echo ""
        read -p "Press Enter to continue after adding the key..."
    fi
fi

# Run migration script
echo "Running API migration..."
python migrate_api.py
echo "✅ API migration completed"
echo ""

# Install web dependencies
echo "Installing web app dependencies..."
cd web
npm install
cd ..
echo "✅ Web dependencies installed"
echo ""

# Start instructions
echo "🎉 Setup complete!"
echo ""
echo "To start the application:"
echo ""
echo "1. In terminal 1, start the API server:"
echo "   $ source venv/bin/activate"
echo "   $ make run-api"
echo ""
echo "2. In terminal 2, start the web app:"
echo "   $ make run-web"
echo ""
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "Available commands:"
echo "  make help         - Show all available commands"
echo "  make test         - Run tests"
echo "  make test-api     - Test API endpoints"
echo "  make analyze      - Analyze a URL interactively"
echo ""
echo "For detailed instructions, see LOCAL_DEVELOPMENT.md"