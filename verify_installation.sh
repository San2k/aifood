#!/bin/bash

# Installation Verification Script
# Checks if all required files are present

echo "AI Nutrition Bot - Installation Verification"
echo "============================================="
echo ""

ERRORS=0

# Check critical files
echo "Checking critical files..."

FILES=(
    "docker-compose.yml"
    ".env.example"
    ".gitignore"
    "README.md"
    "QUICK_START.md"
    "PRE_FLIGHT_CHECKLIST.md"
    "TESTING.md"
    "IMPLEMENTATION_SUMMARY.md"
    "scripts/startup.sh"
    "scripts/stop.sh"
    "services/telegram-bot/src/main.py"
    "services/telegram-bot/Dockerfile"
    "services/telegram-bot/requirements.txt"
    "services/agent-api/src/main.py"
    "services/agent-api/Dockerfile"
    "services/agent-api/requirements.txt"
    "services/agent-api/alembic.ini"
    "services/mcp-fatsecret/src/main.py"
    "services/mcp-fatsecret/Dockerfile"
    "services/mcp-fatsecret/requirements.txt"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ MISSING: $file"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "Checking scripts are executable..."

if [ -x "scripts/startup.sh" ]; then
    echo "  ✅ scripts/startup.sh is executable"
else
    echo "  ⚠️  scripts/startup.sh is not executable (run: chmod +x scripts/startup.sh)"
fi

if [ -x "scripts/stop.sh" ]; then
    echo "  ✅ scripts/stop.sh is executable"
else
    echo "  ⚠️  scripts/stop.sh is not executable (run: chmod +x scripts/stop.sh)"
fi

echo ""
echo "Checking .env configuration..."

if [ -f ".env" ]; then
    echo "  ✅ .env file exists"
    
    # Check for placeholder values
    if grep -q "YOUR_ACTUAL\|YOUR_TELEGRAM\|YOUR_OPENAI\|YOUR_FATSECRET" .env 2>/dev/null; then
        echo "  ⚠️  .env contains placeholder values - please configure with real credentials"
    else
        echo "  ✅ .env appears to be configured"
    fi
else
    echo "  ❌ .env file not found"
    echo "     Create it with: cp .env.example .env"
    echo "     Then edit with your API credentials"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "Checking directory structure..."

DIRS=(
    "services/telegram-bot/src/bot/handlers"
    "services/telegram-bot/src/bot/keyboards"
    "services/telegram-bot/src/services"
    "services/agent-api/src/api/v1/endpoints"
    "services/agent-api/src/graph/nodes"
    "services/agent-api/src/db/models"
    "services/agent-api/src/db/repositories"
    "services/agent-api/src/services"
    "services/agent-api/migrations/versions"
    "services/mcp-fatsecret/src/server/tools"
    "scripts"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir"
    else
        echo "  ❌ MISSING: $dir"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "Checking Docker..."

if command -v docker &> /dev/null; then
    echo "  ✅ Docker is installed"
    
    if docker info &> /dev/null; then
        echo "  ✅ Docker is running"
    else
        echo "  ❌ Docker is not running - please start Docker Desktop"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  ❌ Docker is not installed"
    ERRORS=$((ERRORS + 1))
fi

if command -v docker-compose &> /dev/null; then
    echo "  ✅ docker-compose is installed"
else
    echo "  ❌ docker-compose is not installed"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "============================================="

if [ $ERRORS -eq 0 ]; then
    echo "✅ All checks passed!"
    echo ""
    echo "Next steps:"
    echo "  1. Configure .env with your API keys"
    echo "  2. Run: ./scripts/startup.sh"
    echo "  3. See QUICK_START.md for detailed instructions"
else
    echo "❌ $ERRORS issue(s) found. Please fix before proceeding."
fi

echo ""
