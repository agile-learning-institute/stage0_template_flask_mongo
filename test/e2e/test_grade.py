"""
E2E tests for Grade domain endpoints.

These tests verify that the Grade endpoints work correctly by making
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
def test_grade_get_all_endpoint():
    """Test GET /api/grade endpoint returns list of grades."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/grade", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert isinstance(response.json(), list), "Response should be a list"


@pytest.mark.e2e
def test_grade_get_one_endpoint():
    """Test GET /api/grade/<id> endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    # Try to get a grade (may return 404 if no grades exist, which is fine)
    response = requests.get(f"{BASE_URL}/api/grade/507f1f77bcf86cd799439011", headers=headers)
    # Should return either 200 or 404
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"


@pytest.mark.e2e
def test_grade_endpoints_require_authentication():
    """Test that Grade endpoints require authentication."""
    # Try to access without token
    response = requests.get(f"{BASE_URL}/api/grade")
    assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}"

