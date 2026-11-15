# ─────────────────────────────────────────────────────────────────────
#  Dockerfile — AI Ticket Automation Backend
# ─────────────────────────────────────────────────────────────────────
#  Build:  docker build -t ai-ticket-backend .
#  Run:    docker run -p 8000:8000 --env-file .env ai-ticket-backend
# ─────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Install dependencies (cached layer) ────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy application code ──────────────────────────────────────────
COPY . .

# ── Expose the API port ────────────────────────────────────────────
EXPOSE 8000

# ── Run the server ─────────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
