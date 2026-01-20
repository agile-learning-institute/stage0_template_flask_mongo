"""
Unit tests for Control service.
"""
import unittest
from unittest.mock import patch, MagicMock
from src.services.control_service import ControlService
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound, HTTPInternalServerError


class TestControlService(unittest.TestCase):
    """Test cases for ControlService."""
    
    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id"
        }
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_create_control_success(self, mock_get_mongo, mock_get_config):
        """Test successful creation of a control document."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo
        
        data = {"name": "test-control", "description": "Test control", "status": "active"}
        
        # Act
        control_id = ControlService.create_control(data, self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertEqual(control_id, "123")
        mock_mongo.create_document.assert_called_once()
        call_args = mock_mongo.create_document.call_args
        self.assertEqual(call_args[0][0], "Control")
        created_data = call_args[0][1]
        self.assertIn('created', created_data)
        self.assertIn('saved', created_data)
        self.assertEqual(created_data['name'], "test-control")
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_create_control_removes_id(self, mock_get_mongo, mock_get_config):
        """Test that _id is removed from data before creation."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo
        
        data = {"_id": "should-be-removed", "name": "test"}
        
        # Act
        ControlService.create_control(data, self.mock_token, self.mock_breadcrumb)
        
        # Assert
        call_args = mock_mongo.create_document.call_args
        created_data = call_args[0][1]
        self.assertNotIn('_id', created_data)
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_get_controls_no_filter(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of all control documents."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [
            {"_id": "123", "name": "control1"},
            {"_id": "456", "name": "control2"}
        ]
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        controls = ControlService.get_controls(self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertEqual(len(controls), 2)
        mock_mongo.get_documents.assert_called_once_with("Control")
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_get_controls_with_name_filter(self, mock_get_mongo, mock_get_config):
        """Test retrieval of control documents with name filter."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.find_documents.return_value = [
            {"_id": "123", "name": "test-control"}
        ]
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        controls = ControlService.get_controls(self.mock_token, self.mock_breadcrumb, name="test")
        
        # Assert
        self.assertEqual(len(controls), 1)
        mock_mongo.find_documents.assert_called_once()
        call_args = mock_mongo.find_documents.call_args
        self.assertEqual(call_args[0][0], "Control")
        query = call_args[0][1]
        self.assertIn("name", query)
        self.assertEqual(query["name"]["$regex"], "test")
        self.assertEqual(query["name"]["$options"], "i")
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_get_control_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of a specific control document."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": "123", "name": "control1"}
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        control = ControlService.get_control("123", self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertIsNotNone(control)
        self.assertEqual(control["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("Control", "123")
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_get_control_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_control raises HTTPNotFound when control not found."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPNotFound) as context:
            ControlService.get_control("999", self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_update_control_success(self, mock_get_mongo, mock_get_config):
        """Test successful update of a control document."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {"_id": "123", "name": "updated-control"}
        mock_get_mongo.return_value = mock_mongo
        
        data = {"name": "updated-control", "description": "Updated"}
        
        # Act
        updated = ControlService.update_control("123", data, self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertIsNotNone(updated)
        self.assertEqual(updated["name"], "updated-control")
        mock_mongo.update_document.assert_called_once()
        call_args = mock_mongo.update_document.call_args
        self.assertEqual(call_args[1]["document_id"], "123")
        set_data = call_args[1]["set_data"]
        self.assertIn("saved", set_data)
        self.assertEqual(set_data["name"], "updated-control")
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_update_control_prevent_restricted_fields(self, mock_get_mongo, mock_get_config):
        """Test update_control raises HTTPForbidden when trying to update restricted fields."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo
        
        # Test _id
        data = {"_id": "999", "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            ControlService.update_control("123", data, self.mock_token, self.mock_breadcrumb)
        self.assertIn("_id", str(context.exception))
        
        # Test created
        data = {"created": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            ControlService.update_control("123", data, self.mock_token, self.mock_breadcrumb)
        self.assertIn("created", str(context.exception))
        
        # Test saved
        data = {"saved": {"at_time": "2024-01-01T00:00:00Z"}, "name": "Updated"}
        with self.assertRaises(HTTPForbidden) as context:
            ControlService.update_control("123", data, self.mock_token, self.mock_breadcrumb)
        self.assertIn("saved", str(context.exception))
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_update_control_not_found(self, mock_get_mongo, mock_get_config):
        """Test update_control raises HTTPNotFound when control not found."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = None
        mock_get_mongo.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPNotFound) as context:
            ControlService.update_control("999", {"name": "Updated"}, self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_update_control_handles_missing_ip(self, mock_get_mongo, mock_get_config):
        """Test update_control handles missing from_ip gracefully."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {"_id": "123", "name": "updated"}
        mock_get_mongo.return_value = mock_mongo
        
        breadcrumb_no_ip = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "correlation_id": "test-id"
        }
        
        # Act
        result = ControlService.update_control("123", {"name": "updated"}, self.mock_token, breadcrumb_no_ip)
        
        # Assert
        self.assertIsNotNone(result)
        call_args = mock_mongo.update_document.call_args
        set_data = call_args[1]["set_data"]
        self.assertEqual(set_data["saved"]["Registry"], "127.0.0.1")
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_create_control_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test create_control handles database exceptions."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPInternalServerError):
            ControlService.create_control({"name": "test"}, self.mock_token, self.mock_breadcrumb)
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_get_controls_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_controls handles database exceptions."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_documents.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPInternalServerError):
            ControlService.get_controls(self.mock_token, self.mock_breadcrumb)
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_get_control_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_control handles database exceptions."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPInternalServerError):
            ControlService.get_control("123", self.mock_token, self.mock_breadcrumb)
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_update_control_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test update_control handles database exceptions."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.update_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPInternalServerError):
            ControlService.update_control("123", {"name": "updated"}, self.mock_token, self.mock_breadcrumb)


if __name__ == '__main__':
    unittest.main()
