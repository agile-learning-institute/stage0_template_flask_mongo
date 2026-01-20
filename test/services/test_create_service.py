"""
Unit tests for Create service.
"""
import unittest
from unittest.mock import patch, MagicMock
from src.services.create_service import CreateService
from py_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound, HTTPInternalServerError


class TestCreateService(unittest.TestCase):
    """Test cases for CreateService."""
    
    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id"
        }
    
    @patch('src.services.create_service.Config.get_instance')
    @patch('src.services.create_service.MongoIO.get_instance')
    def test_create_create_success(self, mock_get_mongo, mock_get_config):
        """Test successful creation of a create document."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CREATE_COLLECTION_NAME = "Create"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo
        
        data = {"name": "test-create", "description": "Test create", "status": "active"}
        
        # Act
        create_id = CreateService.create_create(data, self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertEqual(create_id, "123")
        mock_mongo.create_document.assert_called_once()
        call_args = mock_mongo.create_document.call_args
        self.assertEqual(call_args[0][0], "Create")
        created_data = call_args[0][1]
        self.assertIn('created', created_data)
        self.assertEqual(created_data['name'], "test-create")
    
    @patch('src.services.create_service.Config.get_instance')
    @patch('src.services.create_service.MongoIO.get_instance')
    def test_create_create_removes_id(self, mock_get_mongo, mock_get_config):
        """Test that _id is removed from data before creation."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CREATE_COLLECTION_NAME = "Create"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo
        
        data = {"_id": "should-be-removed", "name": "test"}
        
        # Act
        CreateService.create_create(data, self.mock_token, self.mock_breadcrumb)
        
        # Assert
        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertNotIn('_id', created_data)
    
    @patch('src.services.create_service.Config.get_instance')
    @patch('src.services.create_service.MongoIO.get_instance')
    def test_create_create_handles_missing_ip(self, mock_get_mongo, mock_get_config):
        """Test create_create handles missing from_ip gracefully."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CREATE_COLLECTION_NAME = "Create"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo
        
        breadcrumb_no_ip = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "correlation_id": "test-id"
        }
        
        # Act
        result = CreateService.create_create({"name": "test"}, self.mock_token, breadcrumb_no_ip)
        
        # Assert
        self.assertEqual(result, "123")
        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertEqual(created_data["created"]["Registry"], "127.0.0.1")
    
    @patch('src.services.create_service.Config.get_instance')
    @patch('src.services.create_service.MongoIO.get_instance')
    def test_get_creates_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of all create documents."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CREATE_COLLECTION_NAME = "Create"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [
            {"_id": "123", "name": "create1"},
            {"_id": "456", "name": "create2"}
        ]
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        creates = CreateService.get_creates(self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertEqual(len(creates), 2)
        mock_mongo.get_documents.assert_called_once_with("Create")
    
    @patch('src.services.create_service.Config.get_instance')
    @patch('src.services.create_service.MongoIO.get_instance')
    def test_get_create_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of a specific create document."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CREATE_COLLECTION_NAME = "Create"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": "123", "name": "create1"}
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        create = CreateService.get_create("123", self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertIsNotNone(create)
        self.assertEqual(create["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("Create", "123")
    
    @patch('src.services.create_service.Config.get_instance')
    @patch('src.services.create_service.MongoIO.get_instance')
    def test_get_create_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_create raises HTTPNotFound when create not found."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CREATE_COLLECTION_NAME = "Create"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPNotFound) as context:
            CreateService.get_create("999", self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))
    
    @patch('src.services.create_service.Config.get_instance')
    @patch('src.services.create_service.MongoIO.get_instance')
    def test_get_creates_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_creates handles exceptions properly."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CREATE_COLLECTION_NAME = "Create"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_documents.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPInternalServerError):
            CreateService.get_creates(self.mock_token, self.mock_breadcrumb)


if __name__ == '__main__':
    unittest.main()
