#!/bin/bash
set -e

# AiFood Production Deploy Script
# Run on the VPS server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.prod.yml"

cd "$PROJECT_DIR"

echo "=== AiFood Deploy Script ==="
echo "Project directory: $PROJECT_DIR"
echo ""

# Check .env.prod exists
if [ ! -f ".env.prod" ]; then
    echo "ERROR: .env.prod file not found!"
    echo "Create it from .env.example and fill in production values."
    exit 1
fi

# Load production environment
export $(grep -v '^#' .env.prod | xargs)

# Pull latest code
echo "Pulling latest code..."
git fetch origin main
git reset --hard origin/main

# Build and deploy
echo "Building containers..."
docker-compose -f $COMPOSE_FILE build --no-cache

echo "Stopping old containers..."
docker-compose -f $COMPOSE_FILE down

echo "Starting new containers..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services
echo "Waiting for services to start..."
sleep 15

# Run migrations
echo "Running database migrations..."
docker-compose -f $COMPOSE_FILE exec -T agent-api alembic upgrade head

# Health check
echo "Checking health..."
if docker-compose -f $COMPOSE_FILE exec -T agent-api curl -sf http://localhost:8000/health > /dev/null; then
    echo "✓ Agent API is healthy"
else
    echo "✗ Agent API health check failed!"
    docker-compose -f $COMPOSE_FILE logs --tail=50 agent-api
    exit 1
fi

# Cleanup
echo "Cleaning up old images..."
docker image prune -f

echo ""
echo "=== Deploy complete ==="
docker-compose -f $COMPOSE_FILE ps
