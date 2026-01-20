"""
E2E tests for Consume endpoints.

These tests verify that Consume endpoints work correctly by making
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
def test_get_consumes_endpoint():
    """Test GET /api/consume endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/consume", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a list"


@pytest.mark.e2e
def test_get_consumes_with_name_filter():
    """Test GET /api/consume with name query parameter."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/consume?name=test", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a list"


@pytest.mark.e2e
def test_get_consume_not_found():
    """Test GET /api/consume/<id> with non-existent ID."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/consume/000000000000000000000000", headers=headers)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"


@pytest.mark.e2e
def test_consume_endpoints_require_auth():
    """Test that consume endpoints require authentication."""
    # Try without token
    response = requests.get(f"{BASE_URL}/api/consume")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
