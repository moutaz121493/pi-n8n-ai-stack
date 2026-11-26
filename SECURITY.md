# Security & Threat Model

## Design Principles

1. **Zero Open Inbound Ports:** `n8n` binds to `127.0.0.1:5678` by default. Expose webhooks only through Cloudflare Tunnel (with Access/WAF rules) or Tailscale Funnel/Serve.
2. **Secret Hygiene:** Never commit `.env` or exported credentials. `scripts/validate_workflows.py` runs in CI to block common API key and private-IP patterns in workflow JSONs.
3. **Node Isolation:** `N8N_BLOCK_ENV_ACCESS_IN_NODE=true` is enabled in both Compose profiles so untrusted inputs cannot exfiltrate environment secrets via expressions.
4. **Resource Bounds:** Every container defines an explicit `mem_limit` to protect co-hosted services on a Raspberry Pi 5.

## Pre-Production Checklist

- [ ] Generate a unique 32-byte `N8N_ENCRYPTION_KEY` (`openssl rand -hex 32`) and back it up in a password manager.
- [ ] Replace `POSTGRES_PASSWORD` with a unique random secret.
- [ ] Enable n8n user management and 2FA immediately on first login.
- [ ] Put Cloudflare Access or Tailscale ACLs in front of the n8n editor UI while allowing only specific `/webhook/*` paths publicly.
