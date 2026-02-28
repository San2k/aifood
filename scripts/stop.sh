#!/bin/bash

# Stop script for AI Nutrition Bot
# This script stops all services

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping all services...${NC}"
docker-compose down

echo -e "${GREEN}All services stopped!${NC}"
