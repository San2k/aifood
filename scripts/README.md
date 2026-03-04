# Scripts Directory

## Available Scripts

### `openclaw-quick-fix.sh`
**Purpose**: Быстрое обновление Gemini API key во всех конфигурационных файлах OpenClaw

**Usage**:
```bash
./scripts/openclaw-quick-fix.sh <NEW_API_KEY>
```

**Example**:
```bash
./scripts/openclaw-quick-fix.sh AIzaSyC68rf84Zr8a_SUTgLHiAfV8FfDktvlyNs
```

**What it does**:
1. Updates `/root/.openclaw/auth-profiles.json` (root auth)
2. Updates `/root/.openclaw/agents/main/agent/auth-profiles.json` (agent auth - CRITICAL!)
3. Updates `/etc/systemd/system/openclaw-gateway.service` (environment variables)
4. Reloads systemd daemon
5. Restarts OpenClaw Gateway
6. Checks status and logs for errors

**When to use**:
- Gemini API key expired
- Need to switch to a new API key
- "API key invalid" errors in Telegram bot

---

### `setup_gpu_server_ssh.sh`
**Purpose**: SSH setup script for GPU server access

**Location**: Created when needed

---

## Configuration Files Updated

All OpenClaw configuration files are documented in:
- [OPENCLAW_CONFIG.md](../OPENCLAW_CONFIG.md) - Complete configuration guide
- [DEPLOYMENT_STATUS.md](../DEPLOYMENT_STATUS.md) - Deployment status and quick commands

## Server Access

**SSH Alias**: `gpu-server`
**IP**: 199.247.7.186
**User**: root

```bash
ssh gpu-server
```

## Quick Commands

### Check OpenClaw Status
```bash
ssh gpu-server "systemctl status openclaw-gateway"
```

### View Logs
```bash
ssh gpu-server "journalctl -u openclaw-gateway -f"
```

### Check API Key in Use
```bash
ssh gpu-server "cat ~/.openclaw/agents/main/agent/auth-profiles.json | grep key"
```

### Restart OpenClaw
```bash
ssh gpu-server "systemctl restart openclaw-gateway"
```

## Troubleshooting

See [OPENCLAW_CONFIG.md](../OPENCLAW_CONFIG.md) for detailed troubleshooting guide.
