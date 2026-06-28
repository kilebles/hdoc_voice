# ── Stage 1: builder ────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
RUN uv sync --frozen --no-dev


# ── Stage 2: runtime ────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --no-create-home appuser && \
    mkdir -p /app/logs && chown appuser:appgroup /app/logs

COPY --from=builder --chown=appuser:appgroup /app/src ./src/

USER appuser

CMD ["python", "-u", "-m", "src.main"]
