# Production image for the API.
#
# Detection is NOT part of this image: the Ollama vision model runs on the
# photographer's laptop, offline, before anything is uploaded.

FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Dependencies first: this layer is cached until pyproject/uv.lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src ./src
COPY alembic.ini ./
RUN uv sync --frozen --no-dev


FROM python:3.12-slim

# libjpeg/zlib are needed by Pillow at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libjpeg62-turbo zlib1g curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 rpf
WORKDIR /app

COPY --from=builder --chown=rpf:rpf /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=prod \
    STORAGE_BACKEND=s3

USER rpf
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Migrations are run as a separate step before rollout, not on start, so two
# replicas booting at once cannot race each other.
CMD ["uvicorn", "rpf.main:app", "--host", "0.0.0.0", "--port", "8000"]
