FROM python:3.13-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY analytics/ analytics/
COPY configs/ configs/
COPY models/ models/
COPY generate_logs.py .

RUN mkdir -p /data sample_logs

CMD ["sh", "-c", "python generate_logs.py --tasks 50 --out /data/app.log && python -m analytics.ingest /data/ && python -m analytics.report"]