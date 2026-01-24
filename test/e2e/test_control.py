"""
E2E tests for Control endpoints.

These tests verify that Control endpoints work correctly by making
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
def test_create_control_endpoint():
    """Test POST /api/control endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "e2e-test-control",
        "description": "E2E test control document",
        "status": "active"
    }
    
    response = requests.post(f"{BASE_URL}/api/control", headers=headers, json=data)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    
    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data["name"] == "e2e-test-control"
    assert "created" in response_data
    assert "saved" in response_data


@pytest.mark.e2e
def test_get_controls_endpoint():
    """Test GET /api/control endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/control", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    response_data = response.json()
    assert isinstance(response_data, dict), "Response should be a dict (infinite scroll format)"
    assert "items" in response_data, "Response should have 'items' key"
    assert "limit" in response_data, "Response should have 'limit' key"
    assert "has_more" in response_data, "Response should have 'has_more' key"
    assert "next_cursor" in response_data, "Response should have 'next_cursor' key"
    assert isinstance(response_data["items"], list), "Items should be a list"


@pytest.mark.e2e
def test_get_controls_with_name_filter():
    """Test GET /api/control with name query parameter."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/control?name=e2e", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    response_data = response.json()
    assert isinstance(response_data, dict), "Response should be a dict (infinite scroll format)"
    assert "items" in response_data, "Response should have 'items' key"
    assert isinstance(response_data["items"], list), "Items should be a list"


@pytest.mark.e2e
def test_get_control_by_id_endpoint():
    """Test GET /api/control/<id> endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First create a control to get its ID
    data = {"name": "e2e-get-test", "status": "active"}
    create_response = requests.post(f"{BASE_URL}/api/control", headers=headers, json=data)
    assert create_response.status_code == 201
    control_id = create_response.json()["_id"]
    
    # Now get it by ID
    response = requests.get(f"{BASE_URL}/api/control/{control_id}", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    response_data = response.json()
    assert response_data["_id"] == control_id
    assert response_data["name"] == "e2e-get-test"


@pytest.mark.e2e
def test_update_control_endpoint():
    """Test PATCH /api/control/<id> endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First create a control
    data = {"name": "e2e-update-test", "status": "active"}
    create_response = requests.post(f"{BASE_URL}/api/control", headers=headers, json=data)
    assert create_response.status_code == 201
    control_id = create_response.json()["_id"]
    
    # Now update it
    update_data = {"status": "archived", "description": "Updated description"}
    response = requests.patch(f"{BASE_URL}/api/control/{control_id}", headers=headers, json=update_data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    response_data = response.json()
    assert response_data["status"] == "archived"
    assert response_data["description"] == "Updated description"
    assert "saved" in response_data


@pytest.mark.e2e
def test_get_control_not_found():
    """Test GET /api/control/<id> with non-existent ID."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/control/000000000000000000000000", headers=headers)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"


@pytest.mark.e2e
def test_control_endpoints_require_auth():
    """Test that control endpoints require authentication."""
    # Try without token
    response = requests.get(f"{BASE_URL}/api/control")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
