# Build context MUST be the fork root: the sidecar installs ../ (edgartools) as an editable path dep.
#   docker build -f sidecar/Dockerfile -t edgar-sidecar .
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.15 /uv /uvx /usr/local/bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /repo

# library source first (path dep target), then sidecar manifests for layer-cached dep install
COPY pyproject.toml README.md LICENSE.txt /repo/
COPY edgar/ /repo/edgar/
COPY sidecar/pyproject.toml sidecar/uv.lock sidecar/.python-version /repo/sidecar/

WORKDIR /repo/sidecar
RUN uv sync --frozen --no-dev

COPY sidecar/app/ /repo/sidecar/app/

RUN useradd --create-home --uid 10001 sidecar && chown -R sidecar:sidecar /repo
USER sidecar

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('EDGAR_PORT', '8000'), timeout=4)"

CMD ["sh", "-c", "exec /repo/sidecar/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${EDGAR_PORT:-8000}"]
