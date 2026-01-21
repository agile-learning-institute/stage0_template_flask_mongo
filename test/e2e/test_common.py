"""
E2E tests for common endpoints (dev-login, config, metrics).

These tests verify that common endpoints work correctly by making
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
def test_dev_login_endpoint_returns_token():
    """Test that /dev-login endpoint returns a valid token."""
    response = requests.post(
        f"{BASE_URL}/dev-login",
        json={"subject": "e2e-test-user", "roles": ["test"]}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "access_token" in data, "Response missing 'access_token' key"
    assert data["token_type"] == "bearer", "Token type should be 'bearer'"


@pytest.mark.e2e
def test_metrics_endpoint_returns_200():
    """Test that /metrics endpoint returns 200 status."""
    response = requests.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


@pytest.mark.e2e
def test_config_endpoint_returns_200_with_token():
    """Test that /api/config endpoint returns 200 with valid token."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/config", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


@pytest.mark.e2e
def test_config_endpoint_returns_populated_arrays():
    """Test that /api/config endpoint returns non-empty enumerators and versions arrays."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/config", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    
    # Verify enumerators array is not empty
    assert "enumerators" in data, "Response missing 'enumerators' key"
    assert isinstance(data["enumerators"], list), "enumerators should be a list"
    assert len(data["enumerators"]) > 0, "enumerators array should not be empty"
    
    # Verify versions array is not empty
    assert "versions" in data, "Response missing 'versions' key"
    assert isinstance(data["versions"], list), "versions should be a list"
    assert len(data["versions"]) > 0, "versions array should not be empty"

