# AGENTS.md

## Project

- App: Every Seoul backend
- Stack: FastAPI, SQLAlchemy, PostgreSQL, Pydantic
- Frontend repo: `C:\JaeEonYu\dev\every-seoul`

## Commands

- Install dependencies: `python -m pip install -r requirements.txt`
- Run API locally: `uvicorn app.main:app --reload`
- Run tests: `python -m pytest -s tests`
- Compile check: `python -m compileall app`

## Structure

- `app/main.py`: FastAPI app, CORS, health checks
- `app/api/router.py`: API router composition
- `app/api/endpoints`: route handlers
- `app/core/config.py`: environment-backed settings
- `app/db`: SQLAlchemy session and models
- `app/schemas`: Pydantic request/response schemas
- `app/services`: integration and business helpers

## Auth Notes

- Google login is exposed as `POST /api/auth/google`.
- Request body: `{ "credential": "<google-id-token>" }`
- Backend verifies the ID token with `GOOGLE_CLIENT_ID`.
- Existing users are matched by email; missing users are created with empty `districts` and `interests`.
- Frontend sends credentials from Google Identity Services to this endpoint.

## Environment

- Required for Google login: `GOOGLE_CLIENT_ID`
- For local frontend integration, include `http://localhost:5173` and `http://127.0.0.1:5173` in `CORS_ORIGINS`.

## Verification Expectations

Before considering backend work complete:

- `python -m compileall app` should pass.
- `python -m pytest -s tests` should pass or only skip documented integration tests.
- If frontend integration changed, run `pnpm check` in the frontend repo.
