"""
E2E tests for {{item}} endpoints.

These tests verify that {{item}} endpoints work correctly by making
actual HTTP requests to a running server at localhost:{{repo.port}}.

To run these tests:
1. Start the server: pipenv run dev (or pipenv run api for containerized)
2. Run E2E tests: pipenv run e2e
"""
import pytest
import requests

BASE_URL = "http://localhost:{{repo.port}}"


def get_auth_token():
    """Helper function to get an authentication token from dev-login."""
    response = requests.post(
        f"{BASE_URL}/dev-login",
        json={"subject": "e2e-test-user", "roles": ["admin", "developer"]},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


@pytest.mark.e2e
def test_create_{{item | lower}}_endpoint():
    """Test POST /api/{{item | lower}} endpoint and verify record persists in database."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "e2e-test-{{item | lower}}",
        "description": "E2E test {{item | lower}} document",
    }

    response = requests.post(f"{BASE_URL}/api/{{item | lower}}", headers=headers, json=data)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"

    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data["name"] == "e2e-test-{{item | lower}}"
    assert "created" in response_data
    assert "saved" in response_data


@pytest.mark.e2e
def test_get_{{item | lower}}s_endpoint():
    """Test GET /api/{{item | lower}} endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/{{item | lower}}", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    response_data = response.json()
    assert isinstance(response_data, dict), "Response should be a dict (infinite scroll format)"
    assert "items" in response_data, "Response should have 'items' key"
    assert "limit" in response_data, "Response should have 'limit' key"
    assert "has_more" in response_data, "Response should have 'has_more' key"
    assert "next_cursor" in response_data, "Response should have 'next_cursor' key"
    assert isinstance(response_data["items"], list), "Items should be a list"


@pytest.mark.e2e
def test_get_{{item | lower}}s_with_name_filter():
    """Test GET /api/{{item | lower}} with name query parameter."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/{{item | lower}}?name=e2e", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    response_data = response.json()
    assert isinstance(response_data, dict), "Response should be a dict (infinite scroll format)"
    assert "items" in response_data, "Response should have 'items' key"
    assert isinstance(response_data["items"], list), "Items should be a list"


@pytest.mark.e2e
def test_{{item | lower}}_endpoints_require_auth():
    """Test that {{item | lower}} endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/{{item | lower}}")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

