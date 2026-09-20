# syntax=docker/dockerfile:1.7
ARG PYTHON_VERSION=3.12.11

FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ARG UV_VERSION=0.12.15
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /build
RUN python -m pip install "uv==${UV_VERSION}"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable


FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OPSPILOT_ENVIRONMENT=production \
    OPSPILOT_HOST=0.0.0.0 \
    OPSPILOT_PORT=8000

RUN groupadd --gid 10001 opspilot \
    && useradd --uid 10001 --gid opspilot --no-create-home --shell /usr/sbin/nologin opspilot

WORKDIR /app
COPY --from=builder --chown=opspilot:opspilot /build/.venv /app/.venv

USER 10001:10001
EXPOSE 8000
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=2)"]

ENTRYPOINT ["uvicorn"]
CMD ["ops_pilot.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
