# Deployment Notes

## Known-Good Configuration
- Entrypoint: `app.py`
- Deployment run command: `python3 app.py`
- App bind: `host=0.0.0.0`, `port=$PORT` (fallback `8080`)
- Health endpoint: `GET /health` returns HTTP `200`

## Health Check
- Preferred health check path: `/health`
- Protocol is typically internal HTTP in deployment platforms, even when public traffic is HTTPS.

## Common Failures
- `Connection refused`: app process did not start or is not listening on the expected port.
- `500` on health check: wrong probe path or startup error before app becomes ready.
- Crash loop: process exits repeatedly (check deployment startup logs).

## Quick Recovery Steps
1. Ensure deployment runs `python3 app.py`.
2. Ensure app uses platform `PORT` env var.
3. Ensure health check path is `/health`.
4. Stop any duplicate local shell server before republishing.
