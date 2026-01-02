# template_flask_mongo
Python API Template

A minimal Flask + MongoDB API template that follows patterns established in [api_utils](https://github.com/agile-crafts-people/api_utils). This template demonstrates a complete implementation following Creator Dashboard API standards.

## Features

This template implements two domains:

### Grade Domain
- `GET /api/grade` - Get all grades
- `GET /api/grade/<id>` - Get a specific grade by ID

### TestRun Domain
- `POST /api/testrun` - Create a new test run
- `GET /api/testrun` - Get all test runs
- `GET /api/testrun/<id>` - Get a specific test run by ID
- `PATCH /api/testrun/<id>` - Update a test run

### Standard Endpoints
- `/dev-login` - Development JWT token issuance (requires `ENABLE_LOGIN=true`)
- `/api/config` - Configuration endpoint (requires valid JWT token)
- `/metrics` - Prometheus metrics endpoint

## Architecture

The project follows a clean separation of source code and tests:

### Source Code (`src/`)
- **src/server.py** - API entrypoint following py_utils/server.py pattern
- **src/routes/** - HTTP request/response handlers
  - `grade_routes.py` - Grade domain routes
  - `testrun_routes.py` - TestRun domain routes
- **src/services/** - Business logic and RBAC
  - `grade_service.py` - Grade domain service with RBAC
  - `testrun_service.py` - TestRun domain service with RBAC and security checks

### Tests (`test/`)
The test directory mirrors the source structure with a 1-to-1 relationship:
- **test/routes/** - Route unit tests
  - `test_grade_routes.py` - Tests for grade routes
  - `test_testrun_routes.py` - Tests for testrun routes
- **test/services/** - Service unit tests
  - `test_grade_service.py` - Tests for grade service
  - `test_testrun_service.py` - Tests for testrun service
- **test/test_e2e.py** - End-to-end tests flagged with `@pytest.mark.e2e`

## Prerequisites

- Python [v3.12](https://www.python.org/downloads/)
- pipenv [v2026.0.3](https://pipenv.pypa.io/en/latest/installation.html) or newer
- MongoDB (via Docker Compose or local installation)
- SSH access to `git@github.com/agile-crafts-people/api_utils.git`

## Setup

1. **Install dependencies:**
   ```bash
   pipenv install
   ```

2. **Start MongoDB:**
   ```bash
   pipenv run db
   # Or manually: docker-compose up -d mongodb
   ```

3. **Enable dev login (optional but recommended for testing):**
   ```bash
   export ENABLE_LOGIN=true
   ```

4. **Run the development server:**
   ```bash
   pipenv run dev
   ```

   The server will start on port 8184 (EVALUATOR_API_PORT).

## Testing

### Unit Tests
```bash
pipenv run test
```

### E2E Tests
```bash
# In one terminal, start the server:
pipenv run dev

# In another terminal, run E2E tests:
pipenv run e2e
```

## Code Quality

### Format Code
```bash
pipenv run format
```

### Lint Code
```bash
pipenv run lint
```

## Usage Examples

### Get a JWT Token
```bash
TOKEN=$(curl -s -X POST http://localhost:8184/dev-login \
  -H "Content-Type: application/json" \
  -d '{"subject": "user-123", "roles": ["admin", "developer"]}' | jq -r '.access_token')
```

### Create a TestRun
```bash
curl -X POST http://localhost:8184/api/testrun \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Test Run", "status": "pending"}'
```

### Get All Grades
```bash
curl http://localhost:8184/api/grade \
  -H "Authorization: Bearer $TOKEN"
```

## Design Patterns

### RBAC Framework
Services implement simple role-based access control:
- Read operations: Requires authenticated user with any role
- Write operations: Requires `admin` or `developer` role

### Security Checks
- Prevents updates to `_id` field
- Validates permissions before operations
- Uses py_utils custom exceptions for error handling

### Service Layer
Services handle:
- Token and breadcrumb extraction from routes
- RBAC authorization checks
- MongoDB operations via MongoIO singleton
- Business logic validation
- Error handling with appropriate HTTP exceptions

## Standards Compliance

This template follows Creator Dashboard API standards:
- ✅ Config singleton for configuration management
- ✅ MongoIO singleton for MongoDB operations
- ✅ Flask route wrappers for exception handling
- ✅ JWT token authentication
- ✅ Prometheus metrics endpoint
- ✅ Standard pipenv scripts (build, dev, test, e2e)
- ✅ server.py as standard API entry point
- ✅ Separation of routes and services
- ✅ Comprehensive unit and E2E testing

## Project Status

This is a minimal functional template ready for feature-branch continuous improvement workflows. All core functionality is implemented and tested. 
