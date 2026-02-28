#!/bin/bash

# Startup script for AI Nutrition Bot
# This script starts all services and runs database migrations

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}AI Nutrition Bot - Startup Script${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create a .env file with required environment variables."
    echo "See README.md for instructions."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running!${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose down

# Build and start services
echo -e "${YELLOW}Building and starting services...${NC}"
docker-compose up --build -d

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
sleep 5

MAX_RETRIES=30
RETRY_COUNT=0

while ! docker-compose exec -T postgres pg_isready -U nutrition_user > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}Error: PostgreSQL did not start in time${NC}"
        docker-compose logs postgres
        exit 1
    fi
    echo "Waiting for PostgreSQL... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo -e "${GREEN}PostgreSQL is ready!${NC}"

# Wait for Redis to be ready
echo -e "${YELLOW}Waiting for Redis to be ready...${NC}"
sleep 2

RETRY_COUNT=0
while ! docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}Error: Redis did not start in time${NC}"
        docker-compose logs redis
        exit 1
    fi
    echo "Waiting for Redis... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo -e "${GREEN}Redis is ready!${NC}"

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose exec -T agent-api alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Migrations completed successfully!${NC}"
else
    echo -e "${RED}Error running migrations${NC}"
    docker-compose logs agent-api
    exit 1
fi

echo ""
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}All services started successfully!${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""
echo "Services running:"
echo "  - PostgreSQL:   localhost:5432"
echo "  - Redis:        localhost:6379"
echo "  - Agent API:    http://localhost:8000"
echo "  - Telegram Bot: (polling)"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f                # View all logs"
echo "  docker-compose logs -f telegram-bot   # View bot logs"
echo "  docker-compose logs -f agent-api      # View API logs"
echo "  docker-compose down                   # Stop all services"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop following logs...${NC}"
echo ""

# Follow logs
docker-compose logs -f
