"""
Unit tests for Grade routes.
"""
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.grade_routes import create_grade_routes


class TestGradeRoutes(unittest.TestCase):
    """Test cases for Grade routes."""
    
    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_grade_routes(), url_prefix='/api/grade')
        self.client = self.app.test_client()
    
    @patch('src.routes.grade_routes.create_flask_token')
    @patch('src.routes.grade_routes.create_flask_breadcrumb')
    @patch('src.routes.grade_routes.GradeService')
    def test_get_grades_success(self, mock_service_class, mock_create_breadcrumb, mock_create_token):
        """Test GET /api/grade for successful response."""
        # Arrange
        mock_token = {"user_id": "test_user", "roles": ["developer"]}
        mock_create_token.return_value = mock_token
        mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
        mock_create_breadcrumb.return_value = mock_breadcrumb
        
        mock_service = MagicMock()
        mock_service.get_grades.return_value = [{"_id": "123", "name": "Grade A"}]
        mock_service_class.return_value = mock_service
        
        # Act
        response = self.client.get('/api/grade')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        mock_create_token.assert_called_once()
        mock_create_breadcrumb.assert_called_once_with(mock_token)
        mock_service.get_grades.assert_called_once_with(mock_token, mock_breadcrumb)
    
    @patch('src.routes.grade_routes.create_flask_token')
    @patch('src.routes.grade_routes.create_flask_breadcrumb')
    @patch('src.routes.grade_routes.GradeService')
    def test_get_grade_success(self, mock_service_class, mock_create_breadcrumb, mock_create_token):
        """Test GET /api/grade/<id> for successful response."""
        # Arrange
        mock_token = {"user_id": "test_user", "roles": ["developer"]}
        mock_create_token.return_value = mock_token
        mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
        mock_create_breadcrumb.return_value = mock_breadcrumb
        
        mock_service = MagicMock()
        mock_service.get_grade.return_value = {"_id": "123", "name": "Grade A"}
        mock_service_class.return_value = mock_service
        
        # Act
        response = self.client.get('/api/grade/123')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_service.get_grade.assert_called_once_with("123", mock_token, mock_breadcrumb)
    
    @patch('src.routes.grade_routes.create_flask_token')
    @patch('src.routes.grade_routes.create_flask_breadcrumb')
    @patch('src.routes.grade_routes.GradeService')
    def test_get_grade_not_found(self, mock_service_class, mock_create_breadcrumb, mock_create_token):
        """Test GET /api/grade/<id> when grade is not found."""
        # Arrange
        mock_token = {"user_id": "test_user", "roles": ["developer"]}
        mock_create_token.return_value = mock_token
        mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
        mock_create_breadcrumb.return_value = mock_breadcrumb
        
        mock_service = MagicMock()
        mock_service.get_grade.return_value = None
        mock_service_class.return_value = mock_service
        
        # Act
        response = self.client.get('/api/grade/999')
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Grade not found")
    
    @patch('src.routes.grade_routes.create_flask_token')
    def test_get_grades_unauthorized(self, mock_create_token):
        """Test GET /api/grade when token is invalid."""
        # Arrange
        from py_utils.flask_utils.exceptions import HTTPUnauthorized
        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")
        
        # Act
        response = self.client.get('/api/grade')
        
        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == '__main__':
    unittest.main()

