#!/bin/bash
# Quick API health check script

set -e

API_URL="${1:-http://localhost:8000}"
OCR_URL="${2:-http://localhost:8001}"

echo "🔍 Testing AiFood API endpoints..."
echo ""

# Test agent-api health
echo "1️⃣  Testing Agent API health..."
HEALTH=$(curl -s "$API_URL/health")
if echo "$HEALTH" | grep -q '"status":"ok"'; then
    echo "   ✅ Agent API: OK"
    echo "   $HEALTH"
else
    echo "   ❌ Agent API: FAILED"
    exit 1
fi
echo ""

# Test OCR service health
echo "2️⃣  Testing OCR Service health..."
OCR_HEALTH=$(curl -s "$OCR_URL/health" || echo '{"status":"error"}')
if echo "$OCR_HEALTH" | grep -q '"status":"ok"'; then
    echo "   ✅ OCR Service: OK"
    echo "   $OCR_HEALTH"
else
    echo "   ⚠️  OCR Service: Not available (will use Vision fallback)"
    echo "   $OCR_HEALTH"
fi
echo ""

# Test process_label endpoint (mock)
echo "3️⃣  Testing /v1/process_label endpoint..."
PROCESS_RESPONSE=$(curl -s -X POST "$API_URL/v1/process_label" \
  -H "Content-Type: application/json" \
  -d '{
    "odentity": "test_user",
    "photo_url": "https://example.com/test.jpg"
  }' || echo '{"error":"failed"}')

if echo "$PROCESS_RESPONSE" | grep -q '"scan_id"'; then
    SCAN_ID=$(echo "$PROCESS_RESPONSE" | grep -o '"scan_id":"[^"]*"' | cut -d'"' -f4)
    echo "   ✅ Process Label: OK"
    echo "   Scan ID: $SCAN_ID"
else
    echo "   ❌ Process Label: FAILED"
    echo "   Response: $PROCESS_RESPONSE"
fi
echo ""

# Test scan_status endpoint
if [ -n "$SCAN_ID" ]; then
    echo "4️⃣  Testing /v1/scan_status endpoint..."
    STATUS_RESPONSE=$(curl -s "$API_URL/v1/scan_status/$SCAN_ID" || echo '{"error":"failed"}')

    if echo "$STATUS_RESPONSE" | grep -q '"status"'; then
        STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo "   ✅ Scan Status: OK"
        echo "   Status: $STATUS"
    else
        echo "   ❌ Scan Status: FAILED"
        echo "   Response: $STATUS_RESPONSE"
    fi
    echo ""
fi

# Test confirm_message endpoint
echo "5️⃣  Testing /v1/confirm_message endpoint..."
CONFIRM_RESPONSE=$(curl -s -X POST "$API_URL/v1/confirm_message" \
  -H "Content-Type: application/json" \
  -d '{
    "odentity": "test_user",
    "message_text": "подтвердить 150г"
  }' || echo '{"error":"failed"}')

if echo "$CONFIRM_RESPONSE" | grep -q '"action"'; then
    ACTION=$(echo "$CONFIRM_RESPONSE" | grep -o '"action":"[^"]*"' | cut -d'"' -f4)
    echo "   ✅ Confirm Message: OK"
    echo "   Action: $ACTION"
else
    echo "   ❌ Confirm Message: FAILED"
    echo "   Response: $CONFIRM_RESPONSE"
fi
echo ""

echo "✨ API testing complete!"
