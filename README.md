# Template Flask MongoDB API

This is a Flask + MongoDB API template that demonstrates the Creator Dashboard architecture patterns with three domain types: Control (full CRUD), Create (create and read), and Consume (read-only). 

## Prerequisites
- Creator Dashboard [Developers Edition](https://github.com/agile-crafts-people/CreatorDashboard/blob/main/DeveloperEdition/README.md)
- Developer [API Standard Prerequisites](https://github.com/agile-crafts-people/CreatorDashboard/blob/main/DeveloperEdition/standards/api_standards.md)

## Developer Commands

```bash
## Install dependencies
pipenv install

# start backing db container 
# Container Related commands use `de down` before starting the requested containers
pipenv run db

## run unit tests 
pipenv run test

## run api server in dev mode - captures command line, serves API at localhost:8081
pipenv run dev

## run E2E tests (assumes running API at localhost:8081)
pipenv run e2e

## run tests with coverage report
pipenv run coverage

## build application (pre-compiles Python code)
pipenv run build

## build container 
pipenv run container

## Run the backing database and api containers
pipenv run api

## Run the full microservice (db+api+spa)
pipenv run service

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

## API Endpoints

### Control Domain (Full CRUD)
- `POST /api/control` - Create a new control document
- `GET /api/control` - Get all control documents (supports `?name=` query parameter for filtering)
- `GET /api/control/{id}` - Get a specific control document
- `PATCH /api/control/{id}` - Update a control document

### Create Domain (Create + Read)
- `POST /api/create` - Create a new create document
- `GET /api/create` - Get all create documents
- `GET /api/create/{id}` - Get a specific create document

### Consume Domain (Read-only)
- `GET /api/consume` - Get all consume documents
- `GET /api/consume/{id}` - Get a specific consume document

### Common Endpoints
- `GET /docs/index.html` - API Explorer (OpenAPI documentation)
- `POST /dev-login` - Development JWT token issuance (only enabled with `ENABLE_LOGIN=true`)
- `GET /api/config` - Configuration endpoint
- `GET /metrics` - Prometheus metrics

See the [project swagger](./docs/openapi.yaml) for detailed endpoint information.

### Simple Curl Commands:
```bash
# Get a token
export TOKEN=$(curl -s -X POST http://localhost:8081/dev-login \
  -H "Content-Type: application/json" \
  -d '{"subject": "user-123", "roles": ["admin"]}' | jq -r '.access_token')

# Control endpoints
curl http://localhost:8081/api/control \
  -H "Authorization: Bearer $TOKEN"

curl http://localhost:8081/api/control?name=test \
  -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:8081/api/control \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"my-control","description":"Test control","status":"active"}'

curl -X PATCH http://localhost:8081/api/control/{id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status":"archived"}'

# Create endpoints
curl -X POST http://localhost:8081/api/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"my-create","status":"active"}'

curl http://localhost:8081/api/create \
  -H "Authorization: Bearer $TOKEN"

# Consume endpoints
curl http://localhost:8081/api/consume \
  -H "Authorization: Bearer $TOKEN"
```

## RBAC
All services implement a placeholder RBAC pattern for future authorization implementation:
- **Control Service**: Requires valid authentication token (RBAC placeholder for future implementation)
- **Create Service**: Requires valid authentication token (RBAC placeholder for future implementation)
- **Consume Service**: Requires valid authentication token (RBAC placeholder for future implementation)

The RBAC pattern is implemented as `_check_permission()` methods that currently pass through, allowing easy future implementation of role-based access control.
