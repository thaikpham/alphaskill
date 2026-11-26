# api.alphacolorlab.com: the read-only HTTP server (MCP at /mcp, REST at /v1) over the public data-sample/.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 SONY_VN_DATA=/app/data-sample
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
COPY data-sample ./data-sample
RUN uv sync --frozen --no-dev
EXPOSE 8080
CMD ["/app/.venv/bin/sony-alpha-viet-mcp", "--http", "--read-only", "--host", "0.0.0.0", "--port", "8080"]
