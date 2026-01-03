"""
Unit tests for Grade service.
"""
import unittest
from unittest.mock import patch, MagicMock
from src.services.grade_service import GradeService
from py_utils.flask_utils.exceptions import HTTPNotFound, HTTPInternalServerError


class TestGradeService(unittest.TestCase):
    """Test cases for GradeService."""
    
    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
    
    @patch('src.services.grade_service.MongoIO.get_instance')
    def test_get_grades_success(self, mock_get_instance):
        """Test successful retrieval of all grades."""
        # Arrange
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [
            {"_id": "123", "name": "Grade A"},
            {"_id": "456", "name": "Grade B"}
        ]
        mock_get_instance.return_value = mock_mongo
        
        # Act
        grades = GradeService.get_grades(self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertEqual(len(grades), 2)
        mock_mongo.get_documents.assert_called_once_with("Grade")
    
    @patch('src.services.grade_service.MongoIO.get_instance')
    def test_get_grade_success(self, mock_get_instance):
        """Test successful retrieval of a specific grade."""
        # Arrange
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": "123", "name": "Grade A"}
        mock_get_instance.return_value = mock_mongo
        
        # Act
        grade = GradeService.get_grade("123", self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertIsNotNone(grade)
        self.assertEqual(grade["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("Grade", "123")
    
    @patch('src.services.grade_service.MongoIO.get_instance')
    def test_get_grade_not_found(self, mock_get_instance):
        """Test get_grade raises HTTPNotFound when grade not found."""
        # Arrange
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_instance.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPNotFound) as context:
            GradeService.get_grade("999", self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))
    
    @patch('src.services.grade_service.MongoIO.get_instance')
    def test_get_grade_exception(self, mock_get_instance):
        """Test get_grade raises HTTPInternalServerError on exception."""
        # Arrange
        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_instance.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPInternalServerError):
            GradeService.get_grade("123", self.mock_token, self.mock_breadcrumb)


if __name__ == '__main__':
    unittest.main()

