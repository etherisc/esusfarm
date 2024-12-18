ARG DEBIAN_VERSION=bookworm
ARG UV_VERSION=0.5.9
ARG PYTHON_VERSION=3.13

# FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv
FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_VERSION}-${DEBIAN_VERSION}-slim

EXPOSE 8000
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000
ENV MONGO_URL=mongodb://localhost:27017

# copy source code
COPY /app /app
COPY .python-version /app
COPY pyproject.toml /app
COPY uv.lock /app

WORKDIR /app

RUN uv sync --frozen

CMD ["uv", "run", "python3", "main.py"]
