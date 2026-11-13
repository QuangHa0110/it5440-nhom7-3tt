FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY configs ./configs
RUN uv sync --no-dev --frozen

RUN useradd --create-home --uid 10001 triage && mkdir -p /data && chown triage /data
USER triage

ENV PR_TRIAGE_DB=/data/store.sqlite \
    PR_TRIAGE_RULES=/app/configs/semgrep/java-injection.yml \
    PR_TRIAGE_CATALOG=/app/configs/context/java.yml \
    PATH="/app/.venv/bin:${PATH}"

VOLUME /data
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=4).status == 200 else 1)"

CMD ["pr-triage", "serve", "--host", "0.0.0.0", "--port", "8080"]
