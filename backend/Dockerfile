FROM python:3.14-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN uv sync --locked --no-dev


FROM python:3.14-slim AS runtime

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY --from=builder /app/.venv /app/.venv

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts/start.sh ./scripts/start.sh

RUN chown -R appuser:appgroup /app \
    && chmod +x /app/scripts/start.sh

USER appuser

EXPOSE 8000

CMD ["/app/scripts/start.sh"]
