# Research Assistant for PDFs

A React and FastAPI app for uploading one research paper at a time, generating a structured summary, and asking questions about the paper. The summary includes the title, authors, abstract, problem statement, methodology, key results, and conclusion. Chat answers can link to source pages and extracted figures.

## Requirements

- Python 3.12 or 3.13
- Node.js 20.19+ or 22.12+
- An Anthropic API key and a supported Claude model ID

The first run downloads document and embedding models. PDF processing can take several minutes, especially when picture descriptions are enabled.

## Run locally

Run the backend commands from `backend/` so its relative database and upload paths resolve correctly.

### Backend (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Edit `backend/.env` and set `ANTHROPIC_API_KEY` and `CLAUDE_MODEL` to values for your Anthropic account. Leave `ENABLE_PICTURE_DESCRIPTION=false` for the fastest local setup. Then start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Backend (macOS or Linux)

```sh
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
cp .env.example .env
# Set ANTHROPIC_API_KEY and CLAUDE_MODEL in .env.
.venv/bin/python -m uvicorn app.main:app --reload
```

The API listens on `http://127.0.0.1:8000`; `http://127.0.0.1:8000/health` returns `{"status":"ok"}` when it is ready. Keep this terminal running.

### Frontend (second terminal)

```sh
cd frontend
npm ci
npm run dev
```

Open the address printed by Vite, usually `http://127.0.0.1:5173`. Vite proxies `/api` to the local backend; no frontend `.env` file is needed for this setup. Upload a PDF and wait for processing and summary generation to finish, then use the summary, PDF tab, and chat.

## Run checks

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

On macOS or Linux, use `.venv/bin/python -m pytest -q`. From `frontend/`:

```sh
npm test
npm run build
```

The tests use local fixtures and do not require an Anthropic API key.

## Configuration

The backend reads `backend/.env`. `MAX_PDF_PAGES` and `MAX_PDF_SIZE_MB` control upload limits; `RETRIEVAL_K` and `MAX_IMAGES_PER_ANSWER` control how much evidence chat uses. `LANGFUSE_ENABLED` is optional and defaults to `false`; tracing also needs its public and secret keys. Keep `.env` private. Uploaded PDFs, extracted files, and the SQLite database stay under `backend/storage/` and are not committed.

Picture descriptions are optional. Set `ENABLE_PICTURE_DESCRIPTION=true` only when you want to run the local vision model; it can be slow on CPU. Restart the backend after changing `.env`.
