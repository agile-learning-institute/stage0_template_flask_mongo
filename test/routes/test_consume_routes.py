"""
Unit tests for Consume routes.
"""
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.consume_routes import create_consume_routes


class TestConsumeRoutes(unittest.TestCase):
    """Test cases for Consume routes."""
    
    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_consume_routes(), url_prefix='/api/consume')
        self.client = self.app.test_client()
        
        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
    
    @patch('src.routes.consume_routes.create_flask_token')
    @patch('src.routes.consume_routes.create_flask_breadcrumb')
    @patch('src.routes.consume_routes.ConsumeService.get_consumes')
    def test_get_consumes_success(self, mock_get_consumes, mock_create_breadcrumb, mock_create_token):
        """Test GET /api/consume for successful response."""
        # Arrange
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        
        mock_get_consumes.return_value = {
            'items': [
                {"_id": "123", "name": "consume1"},
                {"_id": "456", "name": "consume2"}
            ],
            'limit': 10,
            'has_more': False,
            'next_cursor': None
        }
        
        # Act
        response = self.client.get('/api/consume')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn('items', data)
        self.assertEqual(len(data['items']), 2)
        mock_get_consumes.assert_called_once_with(
            self.mock_token, self.mock_breadcrumb,
            name=None, after_id=None, limit=10, sort_by='name', order='asc'
        )
    
    @patch('src.routes.consume_routes.create_flask_token')
    @patch('src.routes.consume_routes.create_flask_breadcrumb')
    @patch('src.routes.consume_routes.ConsumeService.get_consumes')
    def test_get_consumes_with_name_filter(self, mock_get_consumes, mock_create_breadcrumb, mock_create_token):
        """Test GET /api/consume with name query parameter."""
        # Arrange
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        
        mock_get_consumes.return_value = {
            'items': [{"_id": "123", "name": "test-consume"}],
            'limit': 10,
            'has_more': False,
            'next_cursor': None
        }
        
        # Act
        response = self.client.get('/api/consume?name=test')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn('items', data)
        self.assertEqual(len(data['items']), 1)
        mock_get_consumes.assert_called_once_with(
            self.mock_token, self.mock_breadcrumb,
            name="test", after_id=None, limit=10, sort_by='name', order='asc'
        )
    
    @patch('src.routes.consume_routes.create_flask_token')
    @patch('src.routes.consume_routes.create_flask_breadcrumb')
    @patch('src.routes.consume_routes.ConsumeService.get_consume')
    def test_get_consume_success(self, mock_get_consume, mock_create_breadcrumb, mock_create_token):
        """Test GET /api/consume/<id> for successful response."""
        # Arrange
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        
        mock_get_consume.return_value = {"_id": "123", "name": "consume1"}
        
        # Act
        response = self.client.get('/api/consume/123')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_consume.assert_called_once_with("123", self.mock_token, self.mock_breadcrumb)
    
    @patch('src.routes.consume_routes.create_flask_token')
    @patch('src.routes.consume_routes.create_flask_breadcrumb')
    @patch('src.routes.consume_routes.ConsumeService.get_consume')
    def test_get_consume_not_found(self, mock_get_consume, mock_create_breadcrumb, mock_create_token):
        """Test GET /api/consume/<id> when consume is not found."""
        # Arrange
        from api_utils.flask_utils.exceptions import HTTPNotFound
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        
        mock_get_consume.side_effect = HTTPNotFound("Consume 999 not found")
        
        # Act
        response = self.client.get('/api/consume/999')
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Consume 999 not found")
    
    @patch('src.routes.consume_routes.create_flask_token')
    def test_get_consumes_unauthorized(self, mock_create_token):
        """Test GET /api/consume when token is invalid."""
        # Arrange
        from api_utils.flask_utils.exceptions import HTTPUnauthorized
        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")
        
        # Act
        response = self.client.get('/api/consume')
        
        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)
    
    @patch('src.routes.consume_routes.create_flask_token')
    @patch('src.routes.consume_routes.create_flask_breadcrumb')
    @patch('src.routes.consume_routes.ConsumeService.get_consumes')
    def test_get_consumes_empty_list(self, mock_get_consumes, mock_create_breadcrumb, mock_create_token):
        """Test GET /api/consume when no documents exist."""
        # Arrange
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        
        mock_get_consumes.return_value = []
        
        # Act
        response = self.client.get('/api/consume')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)


if __name__ == '__main__':
    unittest.main()
