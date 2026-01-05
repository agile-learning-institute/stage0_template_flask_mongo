# Evaluator API

This API is responsible for running prompt/model evaluation pipelines. 

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

## run api server in dev mode - captures command line, serves API at localhost:8184
pipenv run dev

## run E2E tests (assumes running API at localhost:8184)
pipenv run e2e

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
See the [project swagger](./docs/openapi.yaml) for information on endpoints. When the API is running an API Explorer is served at [/docs/index.html](http://localhost:8184/docs/index.html)

Simple Curl Commands:
```bash
# Get a token
export TOKEN=$(curl -s -X POST http://localhost:8184/dev-login \
  -H "Content-Type: application/json" \
  -d '{"subject": "user-123", "roles": ["admin"]}' | jq -r '.access_token')

# Use a Token
curl http://localhost:8184/api/config \
  -H "Authorization: Bearer $TOKEN"

curl http://localhost:8184/api/grade \
  -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:8184/api/testrun \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"foo"}'
```

## RBAC
- **Grade Service**: Requires valid authentication token only
- **TestRun Service**: 
  - Read operations: Any authenticated token
  - Write operations (POST, PATCH): Requires `admin` role
