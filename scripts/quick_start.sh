#!/bin/bash
# TOPdesk MCP Python Quick Start Script

set -e

echo "🚀 TOPdesk MCP Python Quick Start"
echo "================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Error: Python 3.11+ required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"

# Install the package
echo "📦 Installing package..."
pip install -e .

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📋 Creating .env from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your TOPdesk credentials before continuing"
    
    # Prompt for credentials
    read -p "Enter your TOPdesk URL (e.g., https://yourcompany.topdesk.net): " TOPDESK_URL
    read -p "Enter your TOPdesk username: " TOPDESK_USERNAME
    read -s -p "Enter your TOPdesk API token: " TOPDESK_PASSWORD
    echo
    
    # Update .env file
    sed -i "s|TOPDESK_URL=.*|TOPDESK_URL=$TOPDESK_URL|" .env
    sed -i "s|TOPDESK_USERNAME=.*|TOPDESK_USERNAME=$TOPDESK_USERNAME|" .env
    sed -i "s|TOPDESK_PASSWORD=.*|TOPDESK_PASSWORD=$TOPDESK_PASSWORD|" .env
    
    echo "✅ Configuration saved to .env"
fi

# Run deployment tests
echo "🧪 Running deployment tests..."
python scripts/test_deployment.py

if [ $? -eq 0 ]; then
    echo
    echo "🎉 Setup complete! You can now run the server:"
    echo
    echo "  # Stdio mode (for MCP clients like Claude Desktop):"
    echo "  topdesk-mcp"
    echo
    echo "  # HTTP mode (for web testing):"
    echo "  TOPDESK_MCP_TRANSPORT=streamable-http topdesk-mcp"
    echo
    echo "  # Docker mode:"
    echo "  docker-compose up"
    echo
    echo "📚 See DEPLOYMENT_GUIDE.md for more deployment options"
else
    echo "❌ Deployment tests failed. Please check the output above."
    exit 1
fi