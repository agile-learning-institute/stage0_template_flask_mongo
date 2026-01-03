# Flask MongoDB API

Flask + MongoDB API following patterns established in [api_utils](https://github.com/agile-crafts-people/api_utils) and Creator Dashboard API standards.

## Prerequisites
- Python [v3.12](https://www.python.org/downloads/)
- pipenv [v2026.0.3](https://pipenv.pypa.io/en/latest/installation.html) or newer
- MongoDB (via Docker Compose or local installation)
- Local clone of [api_utils](https://github.com/agile-crafts-people/api_utils) repository

## Developer Commands

```bash
## Install dependencies
pipenv install

# start backing db container (required for MongoIO unit/integration tests)
pipenv run db

## run unit tests (includes MongoIO Integration Tests)
pipenv run test

## run demo dev server - captures command line, serves API at localhost:8184
export ENABLE_LOGIN=true 
pipenv run dev

## run E2E tests (assumes running API at localhost:8184)
pipenv run e2e

## build package for deployment
pipenv run build

## format code
pipenv run format

## lint code
pipenv run lint
```

## Project Structure

- `src/` - Main package containing:
  - `server.py` - API entrypoint
  - `routes/` - HTTP request/response handlers
  - `services/` - Business logic and RBAC

- `test/` - Test suite with matching directory structure:
  - `routes/` - Route unit tests
  - `services/` - Service unit tests
  - `e2e/` - End-to-end tests flagged with `@pytest.mark.e2e`

## Endpoints

### Grade Domain
- `GET /api/grade` - Get all grades
- `GET /api/grade/<id>` - Get a specific grade by ID

### TestRun Domain
- `POST /api/testrun` - Create a new test run (requires admin role)
- `GET /api/testrun` - Get all test runs
- `GET /api/testrun/<id>` - Get a specific test run by ID
- `PATCH /api/testrun/<id>` - Update a test run (requires admin role)

### Standard Endpoints
- `/dev-login` - Development JWT token issuance (requires `ENABLE_LOGIN=true`)
- `/api/config` - Configuration endpoint (requires valid JWT token)
- `/metrics` - Prometheus metrics endpoint

## Usage

```python
from py_utils import Config, MongoIO, create_flask_token, create_flask_breadcrumb

# Get config singleton
config = Config.get_instance()
print(config.MONGO_DB_NAME)

# Get MongoDB connection singleton
mongo = MongoIO.get_instance()
documents = mongo.get_documents("my_collection")
```

Simple Curl Commands:
```bash
# Get a token
TOKEN=$(curl -s -X POST http://localhost:8184/dev-login \
  -H "Content-Type: application/json" \
  -d '{"subject": "user-123", "roles": ["admin"]}' | jq -r '.access_token')

# Use a Token
curl http://localhost:8184/api/config \
  -H "Authorization: Bearer $TOKEN"
```

## RBAC

- **Grade Service**: Requires valid authentication token only
- **TestRun Service**: 
  - Read operations: Any authenticated token
  - Write operations (POST, PATCH): Requires `admin` role

## Standards Compliance

This API follows Creator Dashboard API standards:
- ✅ Config singleton for configuration management
- ✅ MongoIO singleton for MongoDB operations
- ✅ Flask route wrappers for exception handling
- ✅ JWT token authentication
- ✅ Prometheus metrics endpoint
- ✅ Standard pipenv scripts (build, dev, test, e2e)
- ✅ server.py as standard API entry point
- ✅ Separation of routes and services
- ✅ Comprehensive unit and E2E testing
