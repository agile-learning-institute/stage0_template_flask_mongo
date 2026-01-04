LABEL org.opencontainers.image.source https://github.com/agile-crafts-people/evaluator_api

# Stage 1: Build and compile stage
FROM python:3.12-slim as build

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir pipenv

# Copy dependency files first (for better layer caching)
COPY Pipfile Pipfile.lock ./

# Install dependencies to system Python
# Uses GITHUB_TOKEN from build arg (CI/local with token) or git credentials (local with configured token)
# Standard approach: All installations use HTTPS with GitHub Personal Access Tokens
ARG GITHUB_TOKEN=
RUN if [ -n "$GITHUB_TOKEN" ]; then \
        git config --global url."https://${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"; \
    fi && \
    pipenv install --deploy --system && \
    if [ -n "$GITHUB_TOKEN" ]; then \
        git config --global --unset url."https://${GITHUB_TOKEN}@github.com/".insteadOf; \
    fi

# Copy source code
COPY src/ ./src/

# Generate build timestamp (for consistency with other systems)
RUN DATE=$(date +'%Y%m%d-%H%M%S') && \
    echo "${DATE}" > /app/BUILT_AT

# Pre-compile Python code to bytecode (.pyc files)
RUN pipenv run build

# Stage 2: Production stage
FROM python:3.12-slim

WORKDIR /opt/api_server

# Install runtime dependencies
RUN pip install --no-cache-dir pipenv gunicorn gevent

# Copy dependency files
COPY Pipfile Pipfile.lock ./

# Install production dependencies (no GITHUB_TOKEN needed in production stage - deps already installed)
RUN pipenv install --deploy --system --ignore-pipfile

# Copy compiled code and bytecode from build stage
COPY --from=build /app/src/ ./src/
COPY --from=build /app/BUILT_AT ./

# Set Environment Variables
ENV PYTHONPATH=/opt/api_server
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose the port the app will run on
EXPOSE 8184

# Command to run the application using Gunicorn with exec to forward signals
CMD exec gunicorn --bind 0.0.0.0:8184 src.server:app
