# LegalLens (split: Flask REST API + React app)

```
backend/    Flask REST API (JWT auth, RAG with LangChain + Chroma, SQLAlchemy)
frontend/   React (Vite) single-page app
```

## Run

**Backend** (port 5000)
```
cd backend
python -m venv venv && venv\Scripts\activate      # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                            # macOS/Linux: cp   (then add your GROQ_API_KEY)
python run.py
```
**Frontend** (port 5173, needs Node 18+)
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. Vite proxies `/api` to Flask, so no CORS setup is needed in development.

**Tests:** `cd backend && pytest`

## API (v1, base `/api/v1`)

| Method | Path | Success | Notes |
|---|---|---|---|
| GET | /health | 200 | liveness check |
| POST | /auth/register | 201 | `{email, password}` -> `{user, access_token}` |
| POST | /auth/login | 200 | rate limited |
| GET | /auth/me | 200 | needs `Authorization: Bearer <token>` |
| GET | /documents?page=&per_page= | 200 | `{items, meta}` paginated |
| POST | /documents | 201 | multipart `file`; `Location` header |
| GET | /documents/{id} | 200 | |
| DELETE | /documents/{id} | 204 | removes file, vectors, chats |
| GET | /documents/{id}/messages | 200 | chat history |
| POST | /documents/{id}/messages | 201 | `{question}` -> AI message with sources |
| GET | /documents/{id}/analysis | 200 | summary and risks (cached) |
| POST | /comparisons | 200 | `{document_ids: [a, b]}` |

Errors always look like:
```json
{"error": {"code": "VALIDATION_ERROR", "message": "Some fields are invalid.",
           "details": [{"field": "email", "message": "..."}]}}
```
Status codes used: 400 bad JSON, 401 unauthenticated, 404 not found (also for other users' documents),
409 conflict or not ready, 415 unsupported file, 422 validation, 429 rate limited, 502 AI provider failure.

## Practices applied
Versioned URLs, noun-based resources, correct status codes, one error format, input validation (pydantic),
JWT auth with ownership checks, rate limiting, pagination, CORS allow-list, config classes and env vars,
app factory + blueprints, service layer for AI code, no internal error details leaked, tests.

## Before going to production
Refresh tokens or httpOnly cookies (the token currently lives in localStorage), Alembic migrations,
background jobs for indexing, PostgreSQL + a shared rate-limit store (Redis), Docker, HTTPS, CSRF if cookies are used.
