# Ashes.live API Information

## Summary
Ashes.live API is the backend for a fan-developed deckbuilder and community website for the card game *Ashes Reborn*. It is built using FastAPI and follows a modular structure for models, schemas, and views.

## Structure
- **`api/`**: Main application directory containing the FastAPI app, models, schemas, services, and views.
- **`api/tests/`**: Comprehensive test suite organized by functional area (cards, decks, etc.).
- **`docker/`**: Contains shell scripts for container entrypoints (`entrypoint.sh`, `gunicorn.sh`).
- **`migrations/`**: Alembic migration scripts and environment configuration.
- **`email_templates/`**: HTML templates for various system-generated emails.

## Language & Runtime
**Language**: Python  
**Version**: ^3.10.5 (Dockerfile specifies Python 3.11)  
**Build System**: Poetry  
**Package Manager**: Poetry

## Dependencies
**Main Dependencies**:
- `fastapi`: Web framework for building APIs.
- `sqlalchemy`: SQL Toolkit and Object Relational Mapper.
- `alembic`: Database migrations tool.
- `gunicorn`: WSGI HTTP Server.
- `uvicorn`: ASGI server for FastAPI.
- `psycopg2`: PostgreSQL database adapter.
- `python-jose`: JOSE implementation (JWT).
- `passlib`: Password hashing library.

**Development Dependencies**:
- `pytest`: Testing framework.
- `pytest-cov`: Coverage reporting for pytest.
- `black`: The uncompromising code formatter.
- `isort`: Tool to sort imports.

## Build & Installation
```bash
# Install dependencies using Poetry
poetry install

# Build the Docker stack
make stack

# Rebuild the main app container
make build
```

## Docker

**Dockerfile**: `./Dockerfile`
**Configuration**: Multi-stage build (development and production). It uses `docker-compose.yml` for local development, which includes a `postgres` service and the `api` service. Custom entrypoints are located in `docker/`.

## Testing

**Framework**: Pytest
**Test Location**: `api/tests/`
**Naming Convention**: `test_*.py`
**Configuration**: `.coveragerc` for coverage settings.

**Run Command**:

```bash
# Run the test suite via Docker
make test

# Run tests with specific arguments
make test ARGS='api/tests/cards'
```