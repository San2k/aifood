# Label Recognition Testing Guide

Comprehensive testing for nutrition label recognition feature.

## Prerequisites

```bash
# 1. Start services
docker-compose up -d postgres redis ocr-service agent-api

# 2. Check health
curl http://localhost:8000/health
curl http://localhost:8001/health

# 3. Verify database
docker exec -i aifood-postgres psql -U aifood -d aifood -c "\dt" | grep -E "custom_products|label_scans|food_log_entry"
```

## Quick Tests

### 1. API Health Check
```bash
./scripts/test_api.sh
```

### 2. Integration Test
```bash
cd services/agent-api
pytest tests/integration/test_label_workflow.py -v -s
```

## Manual Test Scenarios

### Scenario 1: Happy Path (OCR Success)

```bash
# Process label
RESPONSE=$(curl -s -X POST http://localhost:8000/v1/process_label \
  -H "Content-Type: application/json" \
  -d '{
    "odentity": "test_user",
    "photo_url": "https://example.com/clear-label.jpg",
    "meal_type": "breakfast"
  }')

SCAN_ID=$(echo $RESPONSE | jq -r '.scan_id')
echo "Scan ID: $SCAN_ID"

# Poll status
while true; do
  STATUS=$(curl -s http://localhost:8000/v1/scan_status/$SCAN_ID | jq -r '.status')
  echo "Status: $STATUS"
  [ "$STATUS" != "processing" ] && break
  sleep 1
done

# View product
curl -s http://localhost:8000/v1/scan_status/$SCAN_ID | jq '.product'

# Confirm
curl -X POST http://localhost:8000/v1/confirm_message \
  -H "Content-Type: application/json" \
  -d '{
    "odentity": "test_user",
    "message_text": "подтвердить 150г"
  }' | jq .
```

**Expected:**
- Product created with `extraction_method: 'paddleocr'`
- Food logged with correct portion

### Scenario 2: Vision Fallback

Use blurry/angled photo to trigger fallback.

**Expected:**
- `extraction_method: 'gemini'`
- Product still successfully created

## Production Deployment

### Deploy to Server

```bash
./scripts/deploy_label_recognition.sh root@199.247.30.52
```

### Post-Deploy Verification

```bash
# Test from server
ssh root@199.247.30.52 "curl -s http://localhost:8000/health | jq ."

# Test from outside
curl -s http://199.247.30.52:8000/health | jq .
```

## Success Criteria

- [  ] All health endpoints return OK
- [ ] OCR service downloads PaddleOCR models successfully
- [ ] Database migrations applied
- [ ] Redis stores/clears pending scans correctly
- [ ] Complete workflow (process → confirm → log) works
- [ ] Vision fallback activates when OCR confidence < 0.75
- [ ] Validation catches invalid nutrition values

---
**Version:** 1.0.0
