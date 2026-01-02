"""
E2E tests for the Flask MongoDB API Template.

These tests verify that the server endpoints work correctly by making
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
def test_testrun_post_endpoint():
    """Test POST /api/testrun endpoint creates a test run."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "E2E Test Run",
        "status": "pending",
        "description": "Created by E2E test"
    }
    response = requests.post(f"{BASE_URL}/api/testrun", json=data, headers=headers)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    
    created = response.json()
    assert "_id" in created, "Response should include _id"
    assert created["name"] == "E2E Test Run", "Name should match"
    
    return created["_id"]


@pytest.mark.e2e
def test_testrun_get_all_endpoint():
    """Test GET /api/testrun endpoint returns list of test runs."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/testrun", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert isinstance(response.json(), list), "Response should be a list"


@pytest.mark.e2e
def test_testrun_get_one_endpoint():
    """Test GET /api/testrun/<id> endpoint."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    # First create a test run
    headers = {"Authorization": f"Bearer {token}"}
    data = {"name": "Test Run for GET", "status": "pending"}
    create_response = requests.post(f"{BASE_URL}/api/testrun", json=data, headers=headers)
    assert create_response.status_code == 201
    testrun_id = create_response.json()["_id"]
    
    # Then retrieve it
    response = requests.get(f"{BASE_URL}/api/testrun/{testrun_id}", headers=headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    retrieved = response.json()
    assert retrieved["_id"] == testrun_id, "Retrieved ID should match"


@pytest.mark.e2e
def test_testrun_patch_endpoint():
    """Test PATCH /api/testrun/<id> endpoint updates a test run."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    # First create a test run
    headers = {"Authorization": f"Bearer {token}"}
    data = {"name": "Test Run for PATCH", "status": "pending"}
    create_response = requests.post(f"{BASE_URL}/api/testrun", json=data, headers=headers)
    assert create_response.status_code == 201
    testrun_id = create_response.json()["_id"]
    
    # Then update it
    update_data = {"name": "Updated Test Run", "status": "completed"}
    response = requests.patch(
        f"{BASE_URL}/api/testrun/{testrun_id}",
        json=update_data,
        headers=headers
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    updated = response.json()
    assert updated["name"] == "Updated Test Run", "Name should be updated"
    assert updated["status"] == "completed", "Status should be updated"


@pytest.mark.e2e
def test_testrun_patch_prevent_id_update():
    """Test PATCH /api/testrun/<id> prevents updating _id field."""
    token = get_auth_token()
    assert token is not None, "Failed to get auth token"
    
    # First create a test run
    headers = {"Authorization": f"Bearer {token}"}
    data = {"name": "Test Run for ID Test"}
    create_response = requests.post(f"{BASE_URL}/api/testrun", json=data, headers=headers)
    assert create_response.status_code == 201
    testrun_id = create_response.json()["_id"]
    
    # Try to update _id (should fail)
    update_data = {"_id": "507f1f77bcf86cd799439011", "name": "Should Fail"}
    response = requests.patch(
        f"{BASE_URL}/api/testrun/{testrun_id}",
        json=update_data,
        headers=headers
    )
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"


@pytest.mark.e2e
def test_testrun_endpoints_require_authentication():
    """Test that TestRun endpoints require authentication."""
    # Try to access without token
    response = requests.get(f"{BASE_URL}/api/testrun")
    assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}"
    
    response = requests.post(f"{BASE_URL}/api/testrun", json={"name": "Test"})
    assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}"


@pytest.mark.e2e
def test_grade_endpoints_require_authentication():
    """Test that Grade endpoints require authentication."""
    # Try to access without token
    response = requests.get(f"{BASE_URL}/api/grade")
    assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}"

