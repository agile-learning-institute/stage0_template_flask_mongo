"""
Unit tests for Consume service.
"""
import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.consume_service import ConsumeService
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound, HTTPInternalServerError
from src.utils.exceptions import HTTPBadRequest


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
    def test_get_consumes_first_batch(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of first batch (no cursor)."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONSUME_COLLECTION_NAME = "Consume"
        mock_get_config.return_value = mock_config
        
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter([
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "consume1"},
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "name": "consume2"}
        ])
        
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        result = ConsumeService.get_consumes(self.mock_token, self.mock_breadcrumb, limit=10)
        
        # Assert
        self.assertIn('items', result)
        self.assertIn('limit', result)
        self.assertIn('has_more', result)
        self.assertIn('next_cursor', result)
        self.assertEqual(len(result['items']), 2)
        self.assertEqual(result['limit'], 10)
        self.assertFalse(result['has_more'])
        self.assertIsNone(result['next_cursor'])
    
    @patch('src.services.consume_service.Config.get_instance')
    @patch('src.services.consume_service.MongoIO.get_instance')
    def test_get_consumes_with_name_filter(self, mock_get_mongo, mock_get_config):
        """Test retrieval of consume documents with name filter."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONSUME_COLLECTION_NAME = "Consume"
        mock_get_config.return_value = mock_config
        
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter([
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "test-consume"}
        ])
        
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        result = ConsumeService.get_consumes(self.mock_token, self.mock_breadcrumb, name="test")
        
        # Assert
        self.assertEqual(len(result['items']), 1)
        # Verify find was called with name filter
        find_call = mock_collection.find.call_args[0][0]
        self.assertIn("name", find_call)
        self.assertEqual(find_call["name"]["$regex"], "test")
        self.assertEqual(find_call["name"]["$options"], "i")
    
    def test_get_consumes_invalid_limit_too_small(self):
        """Test get_consumes raises HTTPBadRequest for limit < 1."""
        with self.assertRaises(HTTPBadRequest) as context:
            ConsumeService.get_consumes(self.mock_token, self.mock_breadcrumb, limit=0)
        self.assertIn("limit must be >= 1", str(context.exception))
    
    def test_get_consumes_invalid_limit_too_large(self):
        """Test get_consumes raises HTTPBadRequest for limit > 100."""
        with self.assertRaises(HTTPBadRequest) as context:
            ConsumeService.get_consumes(self.mock_token, self.mock_breadcrumb, limit=101)
        self.assertIn("limit must be <= 100", str(context.exception))
    
    def test_get_consumes_invalid_sort_by(self):
        """Test get_consumes raises HTTPBadRequest for invalid sort_by."""
        with self.assertRaises(HTTPBadRequest) as context:
            ConsumeService.get_consumes(self.mock_token, self.mock_breadcrumb, sort_by='invalid_field')
        self.assertIn("sort_by must be one of", str(context.exception))
    
    def test_get_consumes_invalid_order(self):
        """Test get_consumes raises HTTPBadRequest for invalid order."""
        with self.assertRaises(HTTPBadRequest) as context:
            ConsumeService.get_consumes(self.mock_token, self.mock_breadcrumb, order='invalid')
        self.assertIn("order must be 'asc' or 'desc'", str(context.exception))
    
    def test_get_consumes_invalid_after_id(self):
        """Test get_consumes raises HTTPBadRequest for invalid after_id."""
        with self.assertRaises(HTTPBadRequest) as context:
            ConsumeService.get_consumes(self.mock_token, self.mock_breadcrumb, after_id='invalid')
        self.assertIn("after_id must be a valid MongoDB ObjectId", str(context.exception))
    
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
        
        mock_collection = MagicMock()
        mock_collection.find.side_effect = Exception("Database error")
        
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
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
