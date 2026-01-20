"""
E2E tests for Create endpoints.

These tests verify that Create endpoints work correctly by making
actual HTTP requests to a running server at localhost:8184.

To run these tests:
1. Start the server: pipenv run dev
2. Run E2E tests: pipenv run e2e
"""
import pytest
import requests

BASE_URL = "http://localhost:8184"


def get_auth_token():
    """Helper function to get an authentication token from dev-login."""
    response = requests.post(
        f"{BASE_URL}/dev-login",
        json={"subject": "e2e-test-user", "roles": ["admin", "developer"]}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


@pytest.mark.e2e
def test_create_create_endpoint():
    """Test POST /api/create endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "e2e-test-create",
        "description": "E2E test create document",
        "status": "active"
    }
    
    response = requests.post(f"{BASE_URL}/api/create", headers=headers, json=data)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    
    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data["name"] == "e2e-test-create"
    assert "created" in response_data


@pytest.mark.e2e
def test_get_creates_endpoint():
    """Test GET /api/create endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/create", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a list"


@pytest.mark.e2e
def test_get_create_by_id_endpoint():
    """Test GET /api/create/<id> endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First create a create document to get its ID
    data = {"name": "e2e-get-test", "status": "active"}
    create_response = requests.post(f"{BASE_URL}/api/create", headers=headers, json=data)
    assert create_response.status_code == 201
    create_id = create_response.json()["_id"]
    
    # Now get it by ID
    response = requests.get(f"{BASE_URL}/api/create/{create_id}", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    response_data = response.json()
    assert response_data["_id"] == create_id
    assert response_data["name"] == "e2e-get-test"


@pytest.mark.e2e
def test_get_create_not_found():
    """Test GET /api/create/<id> with non-existent ID."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/create/000000000000000000000000", headers=headers)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"


@pytest.mark.e2e
def test_create_endpoints_require_auth():
    """Test that create endpoints require authentication."""
    # Try without token
    response = requests.get(f"{BASE_URL}/api/create")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
