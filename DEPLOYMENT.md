# DecisionOS Deployment Guide

This guide details how to deploy DecisionOS in a production environment using Docker and standard orchestration tools.

## Architecture Overview

DecisionOS consists of the following services:
1.  **API Service (`api`)**: FastAPI application handling HTTP requests.
2.  **Worker Service (`worker`)**: Celery worker consuming background tasks.
3.  **Database (`postgres`)**: PostgreSQL 15+ for persistent data.
4.  **Broker/Cache (`redis`)**: Redis for task queue and caching.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- (Optional) Kubernetes cluster 1.25+

## Environment Configuration

Create a `.env` file based on `.env.example`. Critical variables:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `ENV` | Environment mode | `production` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@db:5432/decisionos` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `SECRET_KEY` | Key for cryptographic signing | `openssl rand -hex 32` |

## Docker Compose Deployment (Single Node)

1.  **Build Images**:
    ```bash
    docker-compose build
    ```

2.  **Start Services**:
    ```bash
    docker-compose up -d
    ```

3.  **Run Migrations**:
    ```bash
    # Run migrations using the API container interactively
    docker-compose run --rm api poetry run alembic upgrade head
    ```

## Health Checks

- **API**: GET `/health` (Returns 200 OK)
- **Worker**: Verify process status in simple queue or using Flower (if enabled).

## Scaling Strategy

- **API Layer**: Stateless. Can be horizontally scaled behind a load balancer (e.g., Nginx, AWS ALB).
- **Worker Layer**: Stateless. Scale based on queue depth in Redis.
- **Database**: Use managed services (AWS RDS, Google Cloud SQL) for replication and backups in production.

## Security Considerations

- **SSL/TLS**: Terminate SSL at the load balancer level.
- **Network**: Isolate Redis and Postgres in a private subnet. Only expose the API port (8000).
- **Secrets**: Use Docker Secrets or a Vault in production; do not commit `.env` files.
