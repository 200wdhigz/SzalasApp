#!/bin/bash
# Quick Start Script for Linux/macOS
# Run with: ./setup.sh

set -e

echo "===================================="
echo "SzalasApp Setup Script"
echo "===================================="
echo ""

# Check if Poetry is installed
echo "Checking for Poetry..."
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    echo "Please restart your terminal and run this script again."
    exit 1
else
    echo "Poetry found: $(which poetry)"
fi

# Check Python version
echo ""
echo "Checking Python version..."
python3 --version

# Install dependencies
echo ""
echo "Installing dependencies with Poetry..."
cd app
poetry install
cd ..
echo "Dependencies installed successfully!"

# Create .env file if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ".env file created. Please edit it with your configuration."
else
    echo ".env file already exists."
fi

# Create credentials directory
echo ""
if [ ! -d "credentials" ]; then
    echo "Creating credentials directory..."
    mkdir -p credentials
    echo "Please place your service-account.json in the credentials/ directory."
else
    echo "Credentials directory already exists."
fi

# Summary
echo ""
echo "===================================="
echo "Setup Complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Place service-account.json in credentials/ directory"
echo "3. Run the application:"
echo "   Development: cd app && poetry run python app.py"
echo "   Production:  cd app && poetry run gunicorn --bind 0.0.0.0:8080 app:app"
echo "   Docker:      docker-compose up --build"
echo ""
echo "Documentation:"
echo "  - Poetry Guide: POETRY_GUIDE.md"
echo "  - Docker Guide: DOCKER_GUIDE.md"
echo ""

