"""
E2E tests for TestRun domain endpoints.

These tests verify that the TestRun endpoints work correctly by making
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
        json={"subject": "e2e-test-user", "roles": ["admin"]}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


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
def test_testrun_post_requires_admin_role():
    """Test that POST /api/testrun requires admin role."""
    # Get token without admin role
    response = requests.post(
        f"{BASE_URL}/dev-login",
        json={"subject": "e2e-test-user", "roles": ["developer"]}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {"name": "Test Run"}
    response = requests.post(f"{BASE_URL}/api/testrun", json=data, headers=headers)
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"

