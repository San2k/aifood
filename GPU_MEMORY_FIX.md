# GPU Memory Fix - Out of Memory Error

**Date:** 2026-03-02
**Server:** 199.247.7.186
**Issue:** `cudaMalloc failed: out of memory`

## Problem

OpenClaw Gateway was failing with error:
```
Ollama API error 500: {"error":"llama runner process has terminated: cudaMalloc failed: out of memory"}
```

## Root Cause

Model `qwen-14b-gpu-v2:latest` was configured with:
- `num_ctx=8192` (large context window)
- `num_gpu=30` (30/49 layers on GPU)

Memory allocation breakdown:
```
Model layers (30/49 on GPU):  ~4.6 GB
KV cache (8192 context):      ~3.8 GB (960 MiB × 4)
Compute buffer:               ~0.9 GB
---
TOTAL REQUIRED:               ~9.3 GB
GPU VRAM AVAILABLE:           8.0 GB
---
DEFICIT:                      -1.3 GB ❌
```

**Error logs:**
```
ggml_backend_cuda_buffer_type_alloc_buffer: allocating 3840.00 MiB on device 0: cudaMalloc failed: out of memory
alloc_tensor_range: failed to allocate CUDA0 buffer of size 4026531840
```

## Solution

Created new production model `qwen-prod-gpu:latest` with:
- `num_ctx=4096` (reduced from 8192) ✅
- `num_gpu=30` (same)
- All other params unchanged

Memory allocation after fix:
```
Model layers (30/49 on GPU):  ~4.6 GB
KV cache (4096 context):      ~1.9 GB (480 MiB × 4)
Compute buffer:               ~0.9 GB
---
TOTAL REQUIRED:               ~7.4 GB
GPU VRAM AVAILABLE:           8.0 GB
---
HEADROOM:                     +0.6 GB ✅
```

## Changes Made

### 1. Created Production Model

```bash
cat > /tmp/Modelfile-production << EOF
FROM qwen2.5:14b-instruct

PARAMETER temperature 0.25
PARAMETER num_ctx 4096
PARAMETER num_predict 1024
PARAMETER num_gpu 30

SYSTEM You are Qwen, created by Alibaba Cloud. You are a helpful assistant.
EOF

ollama create qwen-prod-gpu:latest -f /tmp/Modelfile-production
```

### 2. Updated OpenClaw Config

File: `/root/.openclaw/openclaw.json`
```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/qwen-prod-gpu:latest",
        "fallbacks": ["google/gemini-1.5-flash"]
      }
    }
  }
}
```

### 3. Restarted Services

```bash
systemctl restart openclaw-gateway
```

## Verification

### Test Results
```
Model: qwen-prod-gpu:latest
Total duration:       6.03 seconds ✅
Load duration:        2.34 seconds
Prompt eval rate:     49.63 tokens/s
Eval rate:            4.75 tokens/s
GPU memory usage:     ~7.4 GB / 8.0 GB
Status:               No errors ✅
```

### Gateway Status
```
● openclaw-gateway.service - OpenClaw Gateway
   Active: active (running)
   Model: ollama/qwen-prod-gpu:latest ✅
   Plugin: AiFood loaded ✅
   Telegram: @LenoxAI_bot running ✅
```

## Performance Impact

| Metric | Before (ctx=8192) | After (ctx=4096) | Change |
|--------|-------------------|------------------|--------|
| Context window | 8192 tokens | 4096 tokens | -50% |
| Max conversation length | ~6000 words | ~3000 words | -50% |
| Response time | 3.09 sec | 6.03 sec | +95% |
| Memory usage | OUT OF MEMORY ❌ | 7.4 GB / 8 GB ✅ | Working! |
| Reliability | Failing | Stable | ✅ |

**Trade-off:** Reduced context window but **system now works reliably**.

For typical food logging conversations (short messages), 4096 tokens is sufficient.

## Recommendations

### If 4096 context is insufficient:
1. **Reduce GPU layers to 28**: Frees ~400 MB for larger KV cache
2. **Upgrade GPU to 12GB+ VRAM**: Allows both large context and more GPU layers
3. **Use conversation summarization**: Keep only recent context

### For maximum context (8192 tokens):
```bash
# Option 1: Reduce to 28 GPU layers
PARAMETER num_ctx 8192
PARAMETER num_gpu 28

# Option 2: Upgrade to GPU with 12GB+ VRAM
# Then use full 30 layers + 8192 context
```

## Rollback Instructions

If needed to revert:
```bash
# Restore previous config
cp /root/.openclaw/openclaw.json.backup-ctx-fix /root/.openclaw/openclaw.json

# Restart gateway
systemctl restart openclaw-gateway
```

## Monitoring

Check for memory errors:
```bash
# Watch GPU memory
watch -n 1 nvidia-smi

# Monitor Ollama logs
journalctl -u ollama -f | grep -i "error\|cuda"

# Check gateway logs
journalctl -u openclaw-gateway -f
```

## Conclusion

✅ **Issue Resolved**
- Changed `num_ctx` from 8192 to 4096
- Freed ~1.9 GB GPU memory
- System now stable and operational
- Response time: 6.03 seconds (acceptable)
- Trade-off: Shorter context window but reliable operation
