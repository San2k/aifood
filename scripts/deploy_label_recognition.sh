#!/bin/bash
# Production deployment script for AiFood label recognition feature

set -e

SERVER="${1:-root@199.247.30.52}"
PROJECT_DIR="/root/aifood"
SSH_KEY="$HOME/.ssh/weeek_deploy"

echo "🚀 Deploying AiFood Label Recognition to production..."
echo "   Server: $SERVER"
echo "   Directory: $PROJECT_DIR"
echo "   SSH Key: $SSH_KEY"
echo ""

# Function to run command on server
run_on_server() {
    ssh -i "$SSH_KEY" "$SERVER" "$@"
}

# Function to check service health
check_health() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    echo "   Checking $service health..."

    while [ $attempt -le $max_attempts ]; do
        if run_on_server "curl -sf $url" > /dev/null 2>&1; then
            echo "   ✅ $service is healthy"
            return 0
        fi
        echo "   ⏳ Waiting for $service... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    echo "   ❌ $service failed to start"
    return 1
}

# Step 1: Sync code to server
echo "1️⃣  Syncing code to server..."
rsync -avz -e "ssh -i $SSH_KEY" \
    --exclude 'node_modules' --exclude '.git' --exclude '__pycache__' \
    --exclude 'venv' --exclude '*.pyc' --exclude '.pytest_cache' --exclude 'aifood-plugin/dist' \
    ./ "$SERVER:$PROJECT_DIR/"
echo "   ✅ Code synced"
echo ""

# Step 2: Check .env file exists
echo "2️⃣  Checking environment configuration..."
if run_on_server "[ -f $PROJECT_DIR/.env ]"; then
    echo "   ✅ .env file exists"
else
    echo "   ⚠️  .env file not found!"
    echo "   Please create .env file on server with required variables:"
    echo "   - POSTGRES_PASSWORD"
    echo "   - GEMINI_API_KEY"
    exit 1
fi

# Check GEMINI_API_KEY
if run_on_server "grep -q 'GEMINI_API_KEY=' $PROJECT_DIR/.env"; then
    echo "   ✅ GEMINI_API_KEY configured"
else
    echo "   ⚠️  GEMINI_API_KEY not found in .env!"
    echo "   Label recognition requires Gemini Vision API key"
    exit 1
fi
echo ""

# Step 3: Apply database migrations
echo "3️⃣  Applying database migrations..."
run_on_server "cd $PROJECT_DIR && docker-compose up -d postgres"
sleep 5

echo "   Applying 001_add_label_recognition_tables.sql..."
run_on_server "cd $PROJECT_DIR && cat migrations/001_add_label_recognition_tables.sql | docker exec -i aifood-postgres psql -U aifood -d aifood 2>&1" | grep -v "already exists" || true
echo "   ✅ Migrations applied"
echo ""

# Step 4: Build Docker images
echo "4️⃣  Building Docker images..."
echo "   Building ocr-service..."
run_on_server "cd $PROJECT_DIR && docker-compose build ocr-service"
echo "   Building agent-api..."
run_on_server "cd $PROJECT_DIR && docker-compose build agent-api"
echo "   ✅ Images built"
echo ""

# Step 5: Start services
echo "5️⃣  Starting services..."
run_on_server "cd $PROJECT_DIR && docker-compose up -d redis"
run_on_server "cd $PROJECT_DIR && docker-compose up -d ocr-service"
run_on_server "cd $PROJECT_DIR && docker-compose up -d agent-api"
echo "   ✅ Services started"
echo ""

# Step 6: Check service health
echo "6️⃣  Checking service health..."
sleep 10
check_health "Agent API" "http://localhost:8000/health"
check_health "OCR Service" "http://localhost:8001/health" || echo "   ⚠️  OCR Service may still be initializing (downloading models)"
echo ""

# Step 7: Show logs
echo "7️⃣  Recent logs:"
echo ""
echo "   📋 Agent API logs:"
run_on_server "cd $PROJECT_DIR && docker-compose logs --tail=15 agent-api"
echo ""
echo "   📋 OCR Service logs:"
run_on_server "cd $PROJECT_DIR && docker-compose logs --tail=15 ocr-service"
echo ""

# Step 8: Show service status
echo "8️⃣  Service status:"
run_on_server "cd $PROJECT_DIR && docker-compose ps postgres redis ocr-service agent-api"
echo ""

# Step 9: Test endpoints
echo "9️⃣  Testing API endpoints..."
echo "   Testing Agent API health:"
run_on_server "curl -s http://localhost:8000/health | jq ."
echo ""
echo "   Testing OCR Service health:"
run_on_server "curl -s http://localhost:8001/health | jq ." || echo "   (OCR service still initializing)"
echo ""

echo "✨ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Test API: curl http://199.247.30.52:8000/health"
echo "   2. Test label processing: ./scripts/test_api.sh http://199.247.30.52:8000 http://199.247.30.52:8001"
echo "   3. Check logs: ssh $SERVER 'cd $PROJECT_DIR && docker-compose logs -f agent-api'"
echo "   4. Monitor OCR service: ssh $SERVER 'cd $PROJECT_DIR && docker-compose logs -f ocr-service'"
echo ""
echo "🔧 Troubleshooting:"
echo "   - View all logs: ssh $SERVER 'cd $PROJECT_DIR && docker-compose logs'"
echo "   - Restart service: ssh $SERVER 'cd $PROJECT_DIR && docker-compose restart agent-api'"
echo "   - Check Redis: ssh $SERVER 'docker exec -it aifood-redis redis-cli KEYS \"*\"'"
echo ""
