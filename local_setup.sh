#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
echo "Checking required tools..."
if ! command_exists docker; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your actual API keys and configuration"
fi

# Build and start the services
echo "Building and starting services..."
docker-compose build
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Check if services are running
echo "Checking service status..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo "📝 API Documentation: http://localhost:8000/docs"
    echo "🔍 Health Check: http://localhost:8000/health"
    echo "📊 Redis: localhost:6379"
    echo ""
    echo "To view logs:"
    echo "  API logs:     docker-compose logs -f api"
    echo "  Worker logs:  docker-compose logs -f worker"
    echo "  Redis logs:   docker-compose logs -f redis"
    echo ""
    echo "To stop services:"
    echo "  docker-compose stop    (keeps data)"
    echo "  docker-compose down -v (removes data)"
else
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
fi 