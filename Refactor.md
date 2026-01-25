# API Refactor: Server-Side Pagination, Sorting, and Search

## Overview

This refactor adds server-side infinite scroll (cursor-based pagination), sorting, and minimal search capabilities to the list endpoints (`/api/control`, `/api/create`, `/api/consume`).

**Implementation Strategy:**
1. **Phase 1: Implement in template API** - Build concrete implementation in `template_flask_mongo`, test locally
2. **Phase 2: Update SPA** - Update frontend to use new API, test end-to-end
3. **Phase 3: Extract to api_utils** - Once proven, harvest reusable code into `api_utils` for other APIs

**Design Principles:**
- **Minimal search** - Simple name field search only (can be extended per API)
- **Simple implementation first** - Build it concretely, then extract reusable parts later
- **Cursor-based infinite scroll** - Simple, performant, perfect for infinite scroll

**Pre-Determined Decisions (No Approval Required):**
- **Default limit:** 10 items per batch
- **Maximum limit:** 100 items per batch (enforced via validation)
- **Default sort field:** `name`
- **Default sort order:** `asc` (ascending)
- **Allowed sort fields by resource:**
  - Control: `name`, `description`, `status`, `created.at_time`, `saved.at_time`
  - Create: `name`, `description`, `created.at_time`
  - Consume: `name`, `description`
- **Validation approach:** Raise `HTTPBadRequest` exceptions for invalid parameters (no defaulting)
- **Exception handling:** Use try/except ImportError pattern to support Phase 1 (temporary exception) and Phase 3 (api_utils exception)
- **Collection names:** `control`, `create`, `consume` (as established in template)
- **No backward compatibility:** All endpoints return infinite scroll format (no existing deployments)

## Current State

### Current API Behavior

**List Endpoints:**
- `GET /api/control` - Returns all control documents (with optional `name` query parameter)
- `GET /api/create` - Returns all create documents (no search support)
- `GET /api/consume` - Returns all consume documents (with optional `name` query parameter)

**Current Response Format:**
```json
[
  { "_id": "...", "name": "...", ... },
  { "_id": "...", "name": "...", ... }
]
```

**Current Limitations:**
1. No pagination - returns all records
2. No sorting - client must sort
3. Limited search - only `name` parameter on control/consume endpoints
4. No total count - client can't show "X of Y results"

### Current Frontend Behavior

- Fetches all records from API
- Performs sorting client-side via Vuetify `v-data-table`
- Performs pagination client-side via Vuetify `v-data-table`
- Performs search client-side for creates (API doesn't support it)

## Desired State

### New API Behavior

**List Endpoints with Pagination/Sorting:**
- `GET /api/control` - Returns paginated, sorted, filtered results
- `GET /api/create` - Returns paginated, sorted, filtered results (adds search support)
- `GET /api/consume` - Returns paginated, sorted, filtered results

**New Response Format:**
```json
{
  "items": [
    { "_id": "...", "name": "...", ... },
    { "_id": "...", "name": "...", ... }
  ],
  "limit": 10,
  "has_more": true,
  "next_cursor": "last_item_id"  // null if no more items
}
```

**New Query Parameters:**
- `name` - Optional name filter (simple partial match, case-insensitive) - **existing, now works for all endpoints**
- `after_id` - Cursor for infinite scroll (ID of last item from previous batch, omit for first request) - **new**
- `limit` - Items per batch (default: 10, max: 100) - **new**
- `sort_by` - Field to sort by (default: `name`) - **new**
- `order` - Sort order (`asc` or `desc`, default: `asc`) - **new**

**Search Philosophy:**
- **Minimal by default** - Simple name field search only
- **Extensible** - APIs can override/extend search logic if needed
- **Reusable** - Search utilities provided by `api_utils`

## Implementation Plan

### Phase 1: Implement in Template API (Start Here)

**Goal:** Build working implementation in `template_flask_mongo`, test locally, verify it works.

### 1. Update OpenAPI Specification

**File:** `docs/openapi.yaml`

Update all three list endpoints (`/api/control`, `/api/create`, `/api/consume`) to:

1. **Add new query parameters:**
```yaml
parameters:
  - name: name
    in: query
    required: false
    description: Optional name filter (supports partial matches, case-insensitive)
    schema:
      type: string
      example: my-control
  - name: after_id
    in: query
    required: false
    description: Cursor for infinite scroll (ID of last item from previous batch, omit for first request)
    schema:
      type: string
      pattern: '^[0-9a-fA-F]{24}$'
      example: 507f1f77bcf86cd799439011
  - name: limit
    in: query
    required: false
    description: Items per page (max 100)
    schema:
      type: integer
      minimum: 1
      maximum: 100
      default: 10
      example: 10
  - name: sort_by
    in: query
    required: false
    description: Field to sort by (varies by endpoint - see endpoint-specific documentation)
    schema:
      type: string
      # Control endpoint: name, description, status, created.at_time, saved.at_time
      # Create endpoint: name, description, created.at_time
      # Consume endpoint: name, description
      default: name
      example: name
  - name: order
    in: query
    required: false
    description: Sort order
    schema:
      type: string
      enum: [asc, desc]
      default: asc
      example: asc
```

2. **Update response schema:**
```yaml
responses:
  '200':
    description: Successfully retrieved resources
    content:
      application/json:
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                $ref: '#/components/schemas/Control'  # or Create/Consume
            limit:
              type: integer
              description: Items per batch
              example: 10
            has_more:
              type: boolean
              description: Whether there are more items available
              example: true
            next_cursor:
              type: string
              nullable: true
              description: ID of last item for next request (null if no more items)
              pattern: '^[0-9a-fA-F]{24}$'
              example: 507f1f77bcf86cd799439011
```

3. **Add response schema component:**
```yaml
components:
  schemas:
    InfiniteScrollResponse:
      type: object
      required:
        - items
        - limit
        - has_more
        - next_cursor
      properties:
        items:
          type: array
        limit:
          type: integer
        has_more:
          type: boolean
        next_cursor:
          type: string
          nullable: true
```

### 2. Update Route Handlers

**Files to update:**
- `src/routes/control_routes.py`
- `src/routes/create_routes.py`
- `src/routes/consume_routes.py`

**Changes needed:**

1. **Extract and validate query parameters:**
```python
# Get query parameters
name = request.args.get('name')
after_id = request.args.get('after_id')
limit = request.args.get('limit', 10, type=int)
sort_by = request.args.get('sort_by', 'name')
order = request.args.get('order', 'asc')

# Note: Validation happens in service layer, which raises HTTPBadRequest for invalid values
# Route handler just passes parameters through - @handle_route_exceptions will catch exceptions
```

2. **Pass parameters to service:**
```python
result = ControlService.get_controls(
    token, 
    breadcrumb, 
    name=name,
    after_id=after_id,
    limit=limit,
    sort_by=sort_by,
    order=order
)
```

3. **Return infinite scroll response:**
```python
return jsonify(result), 200
```

### 3. Update Service Layer

**Files to update:**
- `src/services/control_service.py`
- `src/services/create_service.py`
- `src/services/consume_service.py`

**Changes needed:**

1. **Update method signatures:**
```python
@staticmethod
def get_controls(token, breadcrumb, name=None, after_id=None, limit=10, sort_by='name', order='asc'):
    """
    Get infinite scroll batch of sorted, filtered control documents.
    
    Args:
        token: Authentication token
        breadcrumb: Audit breadcrumb
        name: Optional name filter (simple search)
        after_id: Cursor (ID of last item from previous batch, None for first request)
        limit: Items per batch
        sort_by: Field to sort by
        order: Sort order ('asc' or 'desc')
    
    Returns:
        dict: {
            'items': [...],
            'limit': int,
            'has_more': bool,
            'next_cursor': str|None  # ID of last item, or None if no more
        }
    """
```

2. **Implement query building and execution (concrete implementation):**
```python
from bson import ObjectId
from src.server import get_db

# Define allowed sort fields for this domain
# Control: name, description, status, created.at_time, saved.at_time
# Create: name, description, created.at_time (no saved field)
# Consume: name, description (no created or saved fields)
ALLOWED_SORT_FIELDS_MAP = {
    'control': ['name', 'description', 'status', 'created.at_time', 'saved.at_time'],
    'create': ['name', 'description', 'created.at_time'],
    'consume': ['name', 'description']
}
# Determine collection name from context (or pass as parameter)
collection_name = 'control'  # or 'create', 'consume' based on service
allowed_fields = ALLOWED_SORT_FIELDS_MAP.get(collection_name, ['name', 'description'])

# Validate inputs - raise exceptions for invalid values
from bson.errors import InvalidId

# Phase 1: Create temporary HTTPBadRequest if not in api_utils yet
# Phase 3: Will import from api_utils.flask_utils.exceptions
try:
    from api_utils.flask_utils.exceptions import HTTPBadRequest
except ImportError:
    # Temporary exception class for Phase 1
    class HTTPBadRequest(Exception):
        status_code = 400
        message = "Bad Request"
        def __init__(self, message=None):
            if message:
                self.message = message
            super().__init__(self.message)

if limit < 1:
    raise HTTPBadRequest("limit must be >= 1")
if limit > 100:
    raise HTTPBadRequest("limit must be <= 100")
if sort_by not in allowed_fields:
    raise HTTPBadRequest(f"sort_by must be one of: {', '.join(allowed_fields)}")
if order not in ['asc', 'desc']:
    raise HTTPBadRequest("order must be 'asc' or 'desc'")

# Validate after_id format if provided
if after_id:
    try:
        ObjectId(after_id)
    except (InvalidId, TypeError):
        raise HTTPBadRequest("after_id must be a valid MongoDB ObjectId")

# Build filter query
filter_query = {}

# Simple name search (minimal - can be extended later)
if name:
    filter_query['name'] = {'$regex': name, '$options': 'i'}

# Add cursor filter if provided (for infinite scroll)
if after_id:
    # For ascending order: get items with _id > after_id
    # For descending order: get items with _id < after_id
    if order == 'asc':
        filter_query['_id'] = {'$gt': ObjectId(after_id)}
    else:
        filter_query['_id'] = {'$lt': ObjectId(after_id)}

# Build sort query
sort_direction = 1 if order == 'asc' else -1
sort_query = {sort_by: sort_direction}

# Get collection
db = get_db()
collection = db['control']  # or 'create', 'consume'

# Execute query - fetch one extra to check if there are more items
cursor = collection.find(filter_query).sort(sort_query).limit(limit + 1)
items = list(cursor)

# Check if there are more items
has_more = len(items) > limit
if has_more:
    items = items[:limit]  # Remove the extra item
    next_cursor = str(items[-1]['_id'])  # ID of last item
else:
    next_cursor = None

return {
    'items': items,
    'limit': limit,
    'has_more': has_more,
    'next_cursor': next_cursor
}
```

**Note:** This is a concrete implementation. Once tested and proven, we'll extract reusable parts to `api_utils` in Phase 3.

### 4. Error Handling and Validation

**No backward compatibility needed** - We have no existing deployments, so all endpoints return the new infinite scroll format.

**Parameter validation:**
- Validate all parameters in service layer
- Raise `HTTPBadRequest` (400) for invalid parameters
- Use sensible defaults for optional parameters (limit=10, sort_by='name', order='asc')


### 5. Error Handling

**Add validation and raise exceptions:**
- Invalid limit values (< 1 or > 100) → `HTTPBadRequest`
- Invalid sort_by fields (not in allowed list) → `HTTPBadRequest`
- Invalid order values (not 'asc' or 'desc') → `HTTPBadRequest`
- Invalid after_id format (not valid ObjectId) → `HTTPBadRequest`

**Exception handling:**
- **Phase 1:** Use local `HTTPBadRequest` exception from `src.utils.exceptions` module (allows testing before harvesting to api_utils)
- **Phase 3:** Replace imports with `HTTPBadRequest` from `api_utils/api_utils/flask_utils/exceptions.py` and remove local module

**Phase 1 implementation (local module):**
```python
# src/utils/exceptions.py (local implementation for Phase 1)
class HTTPBadRequest(Exception):
    status_code = 400
    message = "Bad Request"
    
    def __init__(self, message=None):
        if message:
            self.message = message
        super().__init__(self.message)

# Usage in services:
from src.utils.exceptions import HTTPBadRequest
```

**Exception handling in route wrapper:**
- The `@handle_route_exceptions` decorator from `api_utils` will catch `HTTPBadRequest` exceptions
- It will automatically return appropriate JSON error response with 400 status code

## Testing Requirements

### Unit Tests

**Test cases to add:**

1. **Infinite Scroll:**
   - First request (no after_id) - returns first batch
   - Subsequent requests (with after_id) - returns next batch
   - Last batch (has_more=false, next_cursor=null)
   - Edge cases (limit=0, limit=101, invalid after_id)
   - Empty results (has_more=false, next_cursor=null)

2. **Sorting:**
   - Sort by each allowed field
   - Ascending and descending order
   - Invalid sort_by field (raises HTTPBadRequest)
   - Invalid order value (raises HTTPBadRequest)
   - Nested field sorting (created.at_time, saved.at_time)
   - Cursor works correctly with different sort orders

3. **Search:**
   - Name filter with infinite scroll
   - Name filter with sorting
   - Case-insensitive search
   - Partial match search

4. **Combined:**
   - Search + sorting + infinite scroll together
   - Empty results
   - has_more accuracy (fetch limit+1 to determine)

### Integration Tests

**Test API endpoints:**
```bash
# First batch (infinite scroll)
GET /api/control?limit=10

# Next batch (infinite scroll)
GET /api/control?after_id=507f1f77bcf86cd799439011&limit=10

# Sorting
GET /api/control?sort_by=name&order=asc
GET /api/control?sort_by=created.at_time&order=desc

# Search + Sorting + Infinite Scroll
GET /api/control?name=test&limit=5&sort_by=name&order=asc
GET /api/control?name=test&after_id=507f1f77bcf86cd799439011&limit=5&sort_by=name&order=asc

# All requests return infinite scroll format
GET /api/control  # Returns infinite scroll format (no backward compatibility)
```

## Migration Path

### Phase 1: Backend Implementation (Template API)
1. Update OpenAPI spec
2. Update service layer with concrete pagination/sorting logic
3. Update route handlers
4. Add unit tests
5. Test locally with API explorer/curl
6. **Verify:** API returns correct infinite scroll responses

### Phase 2: Frontend Integration (SPA)
1. template_vue_vuetify/Refactor.md

### Phase 3: Extract to api_utils (Updated Plan)

**Current state (post–Phase 1 & 2):**
- **template_flask_mongo**: All three list endpoints use infinite scroll. Services contain duplicated logic (validation, filter building, sort, query execution, response shaping). `HTTPBadRequest` lives in `src.utils.exceptions` (local).
- **api_utils**: `HTTPBadRequest` already exists in `flask_utils/exceptions.py`. `handle_route_exceptions` does **not** handle `HTTPBadRequest` (only 401/403/404/500); bad-request validation errors would be returned as 500. No infinite-scroll utilities exist yet.

**Phase 3 – Updated steps:**

| Step | Task | Owner / Notes |
|------|------|----------------|
| **3.1** | **Route wrapper**: Add `HTTPBadRequest` handling in `api_utils.flask_utils.route_wrapper` so 400 responses are returned correctly. Add a route-wrapper unit test for `HTTPBadRequest`. | api_utils |
| **3.2** | **Infinite-scroll module**: Create `api_utils.api_utils.mongo_utils.infinite_scroll.py`. Extract a single helper, e.g. `execute_infinite_scroll_query(collection, *, name=None, after_id=None, limit=10, sort_by='name', order='asc', allowed_sort_fields)`. It should: validate params (raise `HTTPBadRequest`), build filter (name regex + cursor), build sort, run `find().sort().limit(limit+1)`, slice and compute `has_more` / `next_cursor`, return `{items, limit, has_more, next_cursor}`. Use `HTTPBadRequest` from `api_utils.flask_utils.exceptions`. | api_utils |
| **3.3** | **Exports**: Export the new function (and any shared types) from `mongo_utils/__init__.py` and document in api_utils README. | api_utils |
| **3.4** | **Unit tests**: Add `tests/mongo_utils/test_infinite_scroll.py` for validation, cursor behaviour, name filter, `has_more` / `next_cursor`, and error cases. | api_utils |
| **3.5** | **Template refactor**: In `template_flask_mongo`, refactor `control_service`, `create_service`, and `consume_service` to call `execute_infinite_scroll_query` with the appropriate `allowed_sort_fields` and collection. Switch all `HTTPBadRequest` imports from `src.utils.exceptions` to `api_utils.flask_utils.exceptions`. | template_flask_mongo |
| **3.6** | **Remove local exception**: Delete `src.utils.exceptions` and `src.utils` if unused. Update template unit tests to import `HTTPBadRequest` from `api_utils`. | template_flask_mongo |
| **3.7** | **Verify**: Run template unit tests, E2E tests, and (if applicable) SPA E2E. Run api_utils tests. Confirm 400 for invalid params and infinite-scroll behaviour end-to-end. | — |
| **3.8** | **Documentation**: Update api_utils README with infinite-scroll usage. Update template README/Refactor notes if needed. | — |

**Reusable pattern (from Phase 1):**  
Validation → filter (name + optional cursor) → sort → `find().sort().limit(limit+1)` → truncate, set `has_more` / `next_cursor` → return `{items, limit, has_more, next_cursor}`. Only `allowed_sort_fields` and collection name vary per domain.

**Why this order?**
- Fix route handling for `HTTPBadRequest` first so 400s are correct.
- Add and test the infinite-scroll helper in api_utils, then refactor the template to use it.
- Remove local exception code only after migration is complete and verified.

## Example Implementation

### Service Method Example (Phase 1 - Concrete Implementation)

```python
@staticmethod
def get_controls(token, breadcrumb, name=None, after_id=None, limit=10, sort_by='name', order='asc'):
    """
    Get infinite scroll batch of sorted, filtered control documents.
    
    Phase 1: Concrete implementation in template API.
    Phase 3: Will be refactored to use api_utils utilities.
    
    Raises:
        HTTPBadRequest: If invalid parameters provided
    """
    from bson import ObjectId
    from bson.errors import InvalidId
    from src.server import get_db
    
    # Phase 1: Create temporary HTTPBadRequest if not in api_utils yet
    # Phase 3: Will import from api_utils.flask_utils.exceptions
    try:
        from api_utils.flask_utils.exceptions import HTTPBadRequest
    except ImportError:
        # Temporary exception class for Phase 1
        class HTTPBadRequest(Exception):
            status_code = 400
            message = "Bad Request"
            def __init__(self, message=None):
                if message:
                    self.message = message
                super().__init__(self.message)
    
    # Define allowed sort fields for this domain
    # Control: name, description, status, created.at_time, saved.at_time
    # Create: name, description, created.at_time (no saved field)
    # Consume: name, description (no created or saved fields)
    ALLOWED_SORT_FIELDS_MAP = {
        'control': ['name', 'description', 'status', 'created.at_time', 'saved.at_time'],
        'create': ['name', 'description', 'created.at_time'],
        'consume': ['name', 'description']
    }
    # Determine collection name from context (or pass as parameter)
    collection_name = 'control'  # or 'create', 'consume' based on service
    allowed_fields = ALLOWED_SORT_FIELDS_MAP.get(collection_name, ['name', 'description'])
    
    # Validate and sanitize inputs
    if limit < 1:
        raise HTTPBadRequest("limit must be >= 1")
    if limit > 100:
        raise HTTPBadRequest("limit must be <= 100")
    if sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPBadRequest(f"sort_by must be one of: {', '.join(ALLOWED_SORT_FIELDS)}")
    if order not in ['asc', 'desc']:
        raise HTTPBadRequest("order must be 'asc' or 'desc'")
    
    # Validate after_id format if provided
    if after_id:
        try:
            ObjectId(after_id)
        except (InvalidId, TypeError):
            raise HTTPBadRequest("after_id must be a valid MongoDB ObjectId")
    
    # Build filter query
    filter_query = {}
    
    # Simple name search (minimal - can be extended later)
    if name:
        filter_query['name'] = {'$regex': name, '$options': 'i'}
    
    # Add cursor filter if provided (for infinite scroll)
    if after_id:
        # For ascending order: get items with _id > after_id
        # For descending order: get items with _id < after_id
        if order == 'asc':
            filter_query['_id'] = {'$gt': ObjectId(after_id)}
        else:
            filter_query['_id'] = {'$lt': ObjectId(after_id)}
    
    # Build sort query
    sort_direction = 1 if order == 'asc' else -1
    sort_query = {sort_by: sort_direction}
    
    # Get collection
    db = get_db()
    collection = db['control']
    
    # Execute query - fetch one extra to check if there are more items
    cursor = collection.find(filter_query).sort(sort_query).limit(limit + 1)
    items = list(cursor)
    
    # Check if there are more items
    has_more = len(items) > limit
    if has_more:
        items = items[:limit]  # Remove the extra item
        next_cursor = str(items[-1]['_id'])  # ID of last item
    else:
        next_cursor = None
    
    return {
        'items': items,
        'limit': limit,
        'has_more': has_more,
        'next_cursor': next_cursor
    }
```

**Phase 1 Note:** 
- Validation raises `HTTPBadRequest` exceptions (create temporary exception class if not in api_utils yet)
- No backward compatibility - always returns infinite scroll format
- All validation happens in service layer

**Phase 3 Note:** Once this is tested and working, we'll:
- Extract query building and execution logic into `api_utils` utilities
- Add `HTTPBadRequest` to `api_utils/api_utils/flask_utils/exceptions.py`
- Refactor service method to use api_utils utilities and exception

### Route Handler Example

```python
@control_routes.route('', methods=['GET'])
@handle_route_exceptions
def get_controls():
    """
    GET /api/control - Retrieve infinite scroll batch of sorted, filtered control documents.
    
    Query Parameters:
        name: Optional name filter
        after_id: Cursor for infinite scroll (ID of last item from previous batch, omit for first request)
        limit: Items per batch (default: 10, max: 100)
        sort_by: Field to sort by (default: 'name')
        order: Sort order 'asc' or 'desc' (default: 'asc')
    
    Returns:
        JSON response with infinite scroll results: {
            'items': [...],
            'limit': int,
            'has_more': bool,
            'next_cursor': str|None
        }
    
    Raises:
        400 Bad Request: If invalid parameters provided
    """
    token = create_flask_token()
    breadcrumb = create_flask_breadcrumb(token)
    
    # Get query parameters
    name = request.args.get('name')
    after_id = request.args.get('after_id')
    limit = request.args.get('limit', 10, type=int)
    sort_by = request.args.get('sort_by', 'name')
    order = request.args.get('order', 'asc')
    
    # Service layer validates parameters and raises HTTPBadRequest if invalid
    # @handle_route_exceptions decorator will catch and format the exception
    result = ControlService.get_controls(
        token, 
        breadcrumb, 
        name=name,
        after_id=after_id,
        limit=limit,
        sort_by=sort_by,
        order=order
    )
    
    logger.info(f"get_controls Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
    return jsonify(result), 200
```

## Notes

- **Implementation Strategy:** Build concrete implementation first, test it, then extract reusable parts to `api_utils`
- **Simplicity:** Single pagination approach (cursor-based infinite scroll) keeps implementation simple
- **Minimal search:** Simple name field search by default - APIs can extend if needed
- **Default values:** Use sensible defaults (limit=10, sort_by='name', order='asc')
- **Max limit:** Enforce maximum limit (100) to prevent abuse
- **Nested fields:** Handle dot notation for nested fields like `created.at_time`
- **Case-insensitive search:** Simple MongoDB regex with `$options: 'i'` for name filter
- **Performance:** Ensure MongoDB indexes on commonly sorted fields (name, created.at_time, etc.) and `_id` for cursor queries
- **Resource-specific sort fields:** Each resource type (control, create, consume) has different allowed sort fields based on their schema
- **Cursor logic:** For ascending order, use `_id > after_id`; for descending, use `_id < after_id`
- **Fetch one extra:** Fetch `limit + 1` items to determine `has_more` without an additional count query
- **No skip() needed:** Cursor-based pagination avoids MongoDB `skip()` which is slow with large offsets
- **Phase 3 extraction:** Once proven, extract query building and execution logic to `api_utils` for reuse

## Success Criteria

### Phase 1: Template API Implementation
- [ ] **OpenAPI spec updated:**
  - [ ] New parameters documented (`after_id`, `limit`, `sort_by`, `order`)
  - [ ] Response format documented
- [ ] **Template API updated:**
  - [ ] All three list endpoints implement infinite scroll
  - [ ] Service methods have concrete implementation
  - [ ] Parameter validation with exception handling
  - [ ] All endpoints return infinite scroll format (no backward compatibility)
- [ ] **Local testing:**
  - [ ] Unit tests for service methods
  - [ ] Integration tests verify API behavior
  - [ ] Tested with API explorer/curl
  - [ ] Verified infinite scroll responses are correct

### Phase 2: Frontend Integration
- [ ] **SPA updated:**
  - [ ] API client supports new parameters
  - [ ] `useResourceList` composable updated for infinite scroll
  - [ ] List pages use infinite scroll
  - [ ] Client-side sorting/pagination removed
- [ ] **End-to-end testing:**
  - [ ] Infinite scroll works in UI
  - [ ] Search works correctly
  - [ ] Sorting works correctly
  - [ ] All edge cases tested

### Phase 3: Extract to api_utils (After Phases 1 & 2 Complete)
- [x] **api_utils updated:**
  - [x] `handle_route_exceptions` handles `HTTPBadRequest` (400); route-wrapper test added
  - [x] `HTTPBadRequest` already in `flask_utils/exceptions.py` (no change)
  - [x] `mongo_utils/infinite_scroll.py` created with `execute_infinite_scroll_query`
  - [x] Unit tests for infinite scroll in `tests/mongo_utils/test_infinite_scroll.py`
  - [x] Exported from `mongo_utils/__init__.py`; api_utils README updated
- [x] **Template API refactored:**
  - [x] Services use `execute_infinite_scroll_query` and `HTTPBadRequest` from api_utils
  - [x] Local `src.utils.exceptions` removed; template tests use api_utils imports
  - [x] Service code simpler after extraction
- [x] **Verification:**
  - [x] Template unit tests pass; route test for 400 Bad Request added
  - [x] api_utils tests pass; 400 for invalid params verified
  - [ ] E2E pass (run `pipenv run db` + `pipenv run dev`, then `pipenv run e2e`)
- [x] **Documentation:** api_utils README and template docs updated; code review done
