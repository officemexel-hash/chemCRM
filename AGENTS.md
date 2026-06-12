# Project Agent Notes

- Canonical GitHub checkout on this workstation: `C:\Users\razor\OneDrive\Desktop\chemCRM`.
- A duplicate/local working copy may exist at `C:\Users\razor\OneDrive\Dokumenty\chemCRM`; do not commit or push from it unless the user explicitly asks.
- Prefer Docker Compose for full app runs, smoke tests, and production-like checks from the repository root:
  - `docker compose up -d --build`
  - `curl http://localhost:8000/health`
  - `curl http://localhost:3000`
  - `docker compose down`
- Do not leave Compose services running after verification unless the user asks to keep them up.
- On Windows, Docker CLI is expected on PATH. If an already-running Codex/PowerShell session does not see it after a PATH update, restart the app/shell or refresh `$env:PATH` from Machine/User environment variables before running Compose.
