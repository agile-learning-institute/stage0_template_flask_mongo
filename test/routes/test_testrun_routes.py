"""
Unit tests for TestRun routes.
"""
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.testrun_routes import create_testrun_routes


class TestTestRunRoutes(unittest.TestCase):
    """Test cases for TestRun routes."""
    
    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_testrun_routes(), url_prefix='/api/testrun')
        self.client = self.app.test_client()
    
    @patch('src.routes.testrun_routes.create_flask_token')
    @patch('src.routes.testrun_routes.create_flask_breadcrumb')
    @patch('src.routes.testrun_routes.TestRunService')
    def test_create_testrun_success(self, mock_service_class, mock_create_breadcrumb, mock_create_token):
        """Test POST /api/testrun for successful creation."""
        # Arrange
        mock_token = {"user_id": "test_user", "roles": ["developer"]}
        mock_create_token.return_value = mock_token
        mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
        mock_create_breadcrumb.return_value = mock_breadcrumb
        
        mock_service = MagicMock()
        mock_service.create_testrun.return_value = "123"
        mock_service.get_testrun.return_value = {"_id": "123", "name": "Test Run 1"}
        mock_service_class.return_value = mock_service
        
        # Act
        response = self.client.post(
            '/api/testrun',
            json={"name": "Test Run 1", "status": "pending"}
        )
        
        # Assert
        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_service.create_testrun.assert_called_once()
        mock_service.get_testrun.assert_called_once_with("123", mock_token, mock_breadcrumb)
    
    @patch('src.routes.testrun_routes.create_flask_token')
    @patch('src.routes.testrun_routes.create_flask_breadcrumb')
    @patch('src.routes.testrun_routes.TestRunService')
    def test_get_testruns_success(self, mock_service_class, mock_create_breadcrumb, mock_create_token):
        """Test GET /api/testrun for successful response."""
        # Arrange
        mock_token = {"user_id": "test_user", "roles": ["developer"]}
        mock_create_token.return_value = mock_token
        mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
        mock_create_breadcrumb.return_value = mock_breadcrumb
        
        mock_service = MagicMock()
        mock_service.get_testruns.return_value = [{"_id": "123", "name": "Test Run 1"}]
        mock_service_class.return_value = mock_service
        
        # Act
        response = self.client.get('/api/testrun')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        mock_service.get_testruns.assert_called_once_with(mock_token, mock_breadcrumb)
    
    @patch('src.routes.testrun_routes.create_flask_token')
    @patch('src.routes.testrun_routes.create_flask_breadcrumb')
    @patch('src.routes.testrun_routes.TestRunService')
    def test_get_testrun_success(self, mock_service_class, mock_create_breadcrumb, mock_create_token):
        """Test GET /api/testrun/<id> for successful response."""
        # Arrange
        mock_token = {"user_id": "test_user", "roles": ["developer"]}
        mock_create_token.return_value = mock_token
        mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
        mock_create_breadcrumb.return_value = mock_breadcrumb
        
        mock_service = MagicMock()
        mock_service.get_testrun.return_value = {"_id": "123", "name": "Test Run 1"}
        mock_service_class.return_value = mock_service
        
        # Act
        response = self.client.get('/api/testrun/123')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_service.get_testrun.assert_called_once_with("123", mock_token, mock_breadcrumb)
    
    @patch('src.routes.testrun_routes.create_flask_token')
    @patch('src.routes.testrun_routes.create_flask_breadcrumb')
    @patch('src.routes.testrun_routes.TestRunService')
    def test_get_testrun_not_found(self, mock_service_class, mock_create_breadcrumb, mock_create_token):
        """Test GET /api/testrun/<id> when test run is not found."""
        # Arrange
        mock_token = {"user_id": "test_user", "roles": ["developer"]}
        mock_create_token.return_value = mock_token
        mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
        mock_create_breadcrumb.return_value = mock_breadcrumb
        
        mock_service = MagicMock()
        mock_service.get_testrun.return_value = None
        mock_service_class.return_value = mock_service
        
        # Act
        response = self.client.get('/api/testrun/999')
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "TestRun not found")
    
    @patch('src.routes.testrun_routes.create_flask_token')
    @patch('src.routes.testrun_routes.create_flask_breadcrumb')
    @patch('src.routes.testrun_routes.TestRunService')
    def test_update_testrun_success(self, mock_service_class, mock_create_breadcrumb, mock_create_token):
        """Test PATCH /api/testrun/<id> for successful update."""
        # Arrange
        mock_token = {"user_id": "test_user", "roles": ["developer"]}
        mock_create_token.return_value = mock_token
        mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
        mock_create_breadcrumb.return_value = mock_breadcrumb
        
        mock_service = MagicMock()
        mock_service.update_testrun.return_value = {"_id": "123", "name": "Updated Test Run"}
        mock_service_class.return_value = mock_service
        
        # Act
        response = self.client.patch(
            '/api/testrun/123',
            json={"name": "Updated Test Run"}
        )
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["name"], "Updated Test Run")
        mock_service.update_testrun.assert_called_once()
    
    @patch('src.routes.testrun_routes.create_flask_token')
    @patch('src.routes.testrun_routes.create_flask_breadcrumb')
    @patch('src.routes.testrun_routes.TestRunService')
    def test_update_testrun_not_found(self, mock_service_class, mock_create_breadcrumb, mock_create_token):
        """Test PATCH /api/testrun/<id> when test run is not found."""
        # Arrange
        mock_token = {"user_id": "test_user", "roles": ["developer"]}
        mock_create_token.return_value = mock_token
        mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
        mock_create_breadcrumb.return_value = mock_breadcrumb
        
        mock_service = MagicMock()
        mock_service.update_testrun.return_value = None
        mock_service_class.return_value = mock_service
        
        # Act
        response = self.client.patch(
            '/api/testrun/999',
            json={"name": "Updated Test Run"}
        )
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "TestRun not found")
    
    @patch('src.routes.testrun_routes.create_flask_token')
    def test_create_testrun_unauthorized(self, mock_create_token):
        """Test POST /api/testrun when token is invalid."""
        # Arrange
        from py_utils.flask_utils.exceptions import HTTPUnauthorized
        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")
        
        # Act
        response = self.client.post('/api/testrun', json={"name": "Test Run"})
        
        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == '__main__':
    unittest.main()

