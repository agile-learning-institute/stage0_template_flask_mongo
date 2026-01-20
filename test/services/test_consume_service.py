"""
Unit tests for Consume service.
"""
import unittest
from unittest.mock import patch, MagicMock
from src.services.consume_service import ConsumeService
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound, HTTPInternalServerError


class TestConsumeService(unittest.TestCase):
    """Test cases for ConsumeService."""
    
    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id"
        }
    
    @patch('src.services.consume_service.Config.get_instance')
    @patch('src.services.consume_service.MongoIO.get_instance')
    def test_get_consumes_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of all consume documents."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONSUME_COLLECTION_NAME = "Consume"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [
            {"_id": "123", "name": "consume1"},
            {"_id": "456", "name": "consume2"}
        ]
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        consumes = ConsumeService.get_consumes(self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertEqual(len(consumes), 2)
        mock_mongo.get_documents.assert_called_once_with("Consume")
    
    @patch('src.services.consume_service.Config.get_instance')
    @patch('src.services.consume_service.MongoIO.get_instance')
    def test_get_consumes_with_name_filter(self, mock_get_mongo, mock_get_config):
        """Test retrieval of consume documents with name filter."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONSUME_COLLECTION_NAME = "Consume"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.find_documents.return_value = [
            {"_id": "123", "name": "test-consume"}
        ]
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        consumes = ConsumeService.get_consumes(self.mock_token, self.mock_breadcrumb, name="test")
        
        # Assert
        self.assertEqual(len(consumes), 1)
        mock_mongo.find_documents.assert_called_once()
        call_args = mock_mongo.find_documents.call_args
        self.assertEqual(call_args[0][0], "Consume")
        query = call_args[0][1]
        self.assertIn("name", query)
        self.assertEqual(query["name"]["$regex"], "test")
        self.assertEqual(query["name"]["$options"], "i")
    
    @patch('src.services.consume_service.Config.get_instance')
    @patch('src.services.consume_service.MongoIO.get_instance')
    def test_get_consume_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of a specific consume document."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONSUME_COLLECTION_NAME = "Consume"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": "123", "name": "consume1"}
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        consume = ConsumeService.get_consume("123", self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertIsNotNone(consume)
        self.assertEqual(consume["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("Consume", "123")
    
    @patch('src.services.consume_service.Config.get_instance')
    @patch('src.services.consume_service.MongoIO.get_instance')
    def test_get_consume_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_consume raises HTTPNotFound when consume not found."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONSUME_COLLECTION_NAME = "Consume"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPNotFound) as context:
            ConsumeService.get_consume("999", self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))
    
    @patch('src.services.consume_service.Config.get_instance')
    @patch('src.services.consume_service.MongoIO.get_instance')
    def test_get_consumes_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_consumes handles exceptions properly."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONSUME_COLLECTION_NAME = "Consume"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_documents.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPInternalServerError):
            ConsumeService.get_consumes(self.mock_token, self.mock_breadcrumb)
    
    @patch('src.services.consume_service.Config.get_instance')
    @patch('src.services.consume_service.MongoIO.get_instance')
    def test_get_consume_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_consume handles exceptions properly."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONSUME_COLLECTION_NAME = "Consume"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPInternalServerError):
            ConsumeService.get_consume("123", self.mock_token, self.mock_breadcrumb)
    
    def test_check_permission_placeholder(self):
        """Test that _check_permission is a placeholder that allows all operations."""
        # This should not raise any exceptions
        ConsumeService._check_permission(self.mock_token, 'read')
        # If we get here without exceptions, the placeholder is working as expected
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
