# ff-backend

Async FastAPI starter project.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Set the following environment variables (e.g., via `.env`) before running the API:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `YOUR_SITE_URL`
- `YOUR_SITE_NAME`

## Development server

```bash
uvicorn app.main:app --reload --port 8000
```

Navigate to `http://localhost:8000/docs` for the interactive Swagger UI.

### Face analysis endpoint

Send an image (multipart form) to `/analyze` to trigger the LLM-backed pipeline:

```bash
curl -X POST \
  -H "Accept: application/json" \
  -F "image=@face.jpg" \
  http://localhost:8000/analyze
```
