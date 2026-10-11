# NaijaVoice AI

A Yoruba-first Nigerian-language AI speech product foundation. This initial release includes a responsive green-and-white landing page, light/dark themes, an editable text-to-speech preview, and a FastAPI health endpoint.

## Run locally on Windows

Prerequisites: Python 3.11+ and Node.js 22.12+ (or Node.js 24), with npm.

In PowerShell, from this project directory:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In a second terminal, from this project directory:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open the local URL printed by Vite (normally http://localhost:5173).
Backend health: http://127.0.0.1:8000/api/health
API documentation: http://127.0.0.1:8000/docs

Expected health response:

```json
{"status":"ok","service":"naijavoice-ai"}
```

## Structure and boundaries

```text
backend/
  app/
    main.py                 # Application factory and composition
    api/router.py           # /api route aggregation
    modules/health/         # Health feature and response model
  tests/test_health.py
frontend/
  src/
    components/             # Shared brand and navigation
    features/landing/       # Landing sections
    features/studio/        # Demo state and language definitions
    App.tsx                 # Page composition
    styles.css              # Theme tokens and responsive styling
```

The backend is a modular monolith: one application, with feature modules mounted through a shared API router. Add future speech capabilities as a separate module, keeping inference adapters behind a service boundary. PostgreSQL persistence can be introduced behind repositories when needed. There are no empty placeholder services or additional infrastructure to run today.

The frontend uses React, TypeScript, Vite, Tailwind CSS v4, and Lucide icons. Tailwind utilities and centralized custom CSS handle layout and theme tokens. Vite proxies `/api` to the local backend for future same-origin API calls.

## Current scope

- Yoruba is the first language in development. Igbo and Hausa are planned.
- Language selection, editable text, character counting, sample reset, section navigation, and theme switching work.
- Theme follows the system on first load; an explicit choice is stored locally.
- Generate speech is intentionally disabled and clearly marked coming soon. Text stays in the browser.
- No AI inference, authentication, database connection, audio playback, or external service calls are implemented. F5-TTS Yoruba and PostgreSQL remain future integrations.

## Verification

```powershell
# From frontend
npm.cmd run build
npm.cmd run preview

# From backend, after creating the virtual environment
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Commit `frontend/package-lock.json` alongside dependency changes. No credentials or environment variables are required for this initial version.
