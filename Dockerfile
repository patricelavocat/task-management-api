# ===================================== Build Image ===============================================
# Inspired by https://github.com/astral-sh/uv-docker-example/blob/main/multistage.Dockerfile
ARG CONTAINER_REGISTRY=docker.io
FROM ${CONTAINER_REGISTRY}/astral/uv:0.8-python3.13-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Disable Python downloads, because we want to use the system interpreter
# across both images. If using a managed Python version, it needs to be
# copied from the build image into the final image; see `standalone.Dockerfile`
# for an example.
ENV UV_PYTHON_DOWNLOADS=0


WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ===================================== Development Image =========================================
# Development image with uv and dev dependencies for running tests
FROM ${CONTAINER_REGISTRY}/astral/uv:0.8-python3.13-bookworm-slim AS development

ARG PROJECT_NAME=task-management-api
ARG UID_AND_GID=10001
ARG USERNAME=${PROJECT_NAME}-user
ARG GROUPNAME=${PROJECT_NAME}-group

ENV UV_PYTHON_DOWNLOADS=0
ENV PYTHONPATH="/app"

WORKDIR /app

# Install tini for proper signal handling
RUN apt-get update && apt-get -y install --no-install-recommends tini && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create user
RUN addgroup --gid=$UID_AND_GID $GROUPNAME \
    && useradd -m --system --uid=$UID_AND_GID -g $GROUPNAME $USERNAME

# Copy project files
COPY --chown=$USERNAME:$GROUPNAME . /app

# Install all dependencies including dev dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Set proper permissions
RUN chown -R $USERNAME:$GROUPNAME /app/.venv

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Switch to the created user
USER $USERNAME

# Default command for development (can be overridden)
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uv", "run", "pytest"]

# ===================================== Run Image =================================================
# Then, use a final image without uv
FROM ${CONTAINER_REGISTRY}/python:3.13-slim-bookworm AS production

ARG PROJECT_NAME=task-management-api
ARG UID_AND_GID=10001
ARG USERNAME=${PROJECT_NAME}-user
ARG GROUPNAME=${PROJECT_NAME}-group

WORKDIR /app

# Install tini for proper signal handling
RUN apt-get update && apt-get -y install --no-install-recommends tini && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create user
RUN addgroup --gid=$UID_AND_GID $GROUPNAME \
    && useradd -m --system --uid=$UID_AND_GID -g $GROUPNAME $USERNAME

# Copy application from builder
COPY --from=builder --chown=$USERNAME:$GROUPNAME /app /app
RUN chown -R $USERNAME:$GROUPNAME /app/.venv

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Copy entrypoint and give execution rights
COPY --chown=$USERNAME:$GROUPNAME docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Switch to the created user
USER $USERNAME

# Entrypoint
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["docker-entrypoint.sh"]
