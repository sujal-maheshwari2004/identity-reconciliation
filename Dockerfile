# ─── Stage 1: Builder ─────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv for faster dependency installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY requirements.txt .

RUN uv pip install --system --no-cache -r requirements.txt


# ─── Stage 2: Runtime ─────────────────────────────────────────────
FROM python:3.13-slim

WORKDIR /app

# Create non-root user
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/
COPY migrations/ ./migrations/

# Set proper permissions
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
