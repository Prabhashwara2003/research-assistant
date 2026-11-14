# Research Assistant frontend

React, TypeScript, Vite, Tailwind CSS, and the browser's PDF viewer. Requires Node.js 20.19+ or 22.12+ and the FastAPI backend.

## Run locally

1. Start the backend from `backend/` using its Python environment: `python -m uvicorn app.main:app --reload`.
2. From `frontend/`, run `npm install` and `npm run dev`.
3. Open the address printed by Vite, normally `http://127.0.0.1:5173`.

The Vite server proxies `/api` requests to `http://127.0.0.1:8000`, so no backend CORS change is needed. If using another backend URL, set `VITE_API_BASE_URL` in `frontend/.env.local` (see `.env.example`). That URL must allow the frontend origin through CORS. Keep AI credentials in the backend only.

Upload a PDF, wait for processing and summary generation, then read the summary or original PDF and ask questions. The last document ID is saved locally so a refresh can restore the paper and its conversation. Select **Upload new PDF** to start over.

## Checks

Run `npm run typecheck`, `npm test`, and `npm run build` from `frontend/`. The build output is in `dist/`.
