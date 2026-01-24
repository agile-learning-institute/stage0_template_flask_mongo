"""
Unit tests for Control service.
"""
import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.control_service import ControlService
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound, HTTPInternalServerError
from src.utils.exceptions import HTTPBadRequest


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
    def test_get_controls_first_batch(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of first batch (no cursor)."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter([
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "control1"},
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "name": "control2"}
        ])
        
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        result = ControlService.get_controls(self.mock_token, self.mock_breadcrumb, limit=10)
        
        # Assert
        self.assertIn('items', result)
        self.assertIn('limit', result)
        self.assertIn('has_more', result)
        self.assertIn('next_cursor', result)
        self.assertEqual(len(result['items']), 2)
        self.assertEqual(result['limit'], 10)
        self.assertFalse(result['has_more'])
        self.assertIsNone(result['next_cursor'])
        mock_collection.find.assert_called_once()
        mock_cursor.sort.assert_called_once()
        mock_cursor.limit.assert_called_once_with(11)  # limit + 1
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_get_controls_with_name_filter(self, mock_get_mongo, mock_get_config):
        """Test retrieval of control documents with name filter."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter([
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "test-control"}
        ])
        
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        result = ControlService.get_controls(self.mock_token, self.mock_breadcrumb, name="test")
        
        # Assert
        self.assertEqual(len(result['items']), 1)
        # Verify find was called with name filter
        find_call = mock_collection.find.call_args[0][0]
        self.assertIn("name", find_call)
        self.assertEqual(find_call["name"]["$regex"], "test")
        self.assertEqual(find_call["name"]["$options"], "i")
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_get_controls_with_cursor(self, mock_get_mongo, mock_get_config):
        """Test retrieval with cursor (after_id)."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        after_id = "507f1f77bcf86cd799439011"
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter([
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "name": "control2"},
            {"_id": ObjectId("507f1f77bcf86cd799439013"), "name": "control3"}
        ])
        
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        result = ControlService.get_controls(self.mock_token, self.mock_breadcrumb, after_id=after_id, limit=10)
        
        # Assert
        self.assertEqual(len(result['items']), 2)
        # Verify find was called with _id filter for ascending order
        find_call = mock_collection.find.call_args[0][0]
        self.assertIn("_id", find_call)
        self.assertIn("$gt", find_call["_id"])
    
    @patch('src.services.control_service.Config.get_instance')
    @patch('src.services.control_service.MongoIO.get_instance')
    def test_get_controls_has_more(self, mock_get_mongo, mock_get_config):
        """Test has_more flag when more items exist."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        # Return 11 items (limit + 1) to trigger has_more
        items = [
            {"_id": ObjectId(f"507f1f77bcf86cd7994390{i:02d}"), "name": f"control{i}"}
            for i in range(11)
        ]
        mock_cursor.__iter__ = lambda self: iter(items)
        
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo
        
        # Act
        result = ControlService.get_controls(self.mock_token, self.mock_breadcrumb, limit=10)
        
        # Assert
        self.assertEqual(len(result['items']), 10)  # Should be truncated to limit
        self.assertTrue(result['has_more'])
        self.assertIsNotNone(result['next_cursor'])
        # The next_cursor should be the ID of the 10th item (index 9)
        self.assertEqual(result['next_cursor'], str(items[9]['_id']))
    
    def test_get_controls_invalid_limit_too_small(self):
        """Test get_controls raises HTTPBadRequest for limit < 1."""
        with self.assertRaises(HTTPBadRequest) as context:
            ControlService.get_controls(self.mock_token, self.mock_breadcrumb, limit=0)
        self.assertIn("limit must be >= 1", str(context.exception))
    
    def test_get_controls_invalid_limit_too_large(self):
        """Test get_controls raises HTTPBadRequest for limit > 100."""
        with self.assertRaises(HTTPBadRequest) as context:
            ControlService.get_controls(self.mock_token, self.mock_breadcrumb, limit=101)
        self.assertIn("limit must be <= 100", str(context.exception))
    
    def test_get_controls_invalid_sort_by(self):
        """Test get_controls raises HTTPBadRequest for invalid sort_by."""
        with self.assertRaises(HTTPBadRequest) as context:
            ControlService.get_controls(self.mock_token, self.mock_breadcrumb, sort_by='invalid_field')
        self.assertIn("sort_by must be one of", str(context.exception))
    
    def test_get_controls_invalid_order(self):
        """Test get_controls raises HTTPBadRequest for invalid order."""
        with self.assertRaises(HTTPBadRequest) as context:
            ControlService.get_controls(self.mock_token, self.mock_breadcrumb, order='invalid')
        self.assertIn("order must be 'asc' or 'desc'", str(context.exception))
    
    def test_get_controls_invalid_after_id(self):
        """Test get_controls raises HTTPBadRequest for invalid after_id."""
        with self.assertRaises(HTTPBadRequest) as context:
            ControlService.get_controls(self.mock_token, self.mock_breadcrumb, after_id='invalid')
        self.assertIn("after_id must be a valid MongoDB ObjectId", str(context.exception))
    
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
    def test_update_control_uses_breadcrumb_directly(self, mock_get_mongo, mock_get_config):
        """Test update_control uses breadcrumb directly for saved field."""
        # Arrange
        mock_config = MagicMock()
        mock_config.CONTROL_COLLECTION_NAME = "Control"
        mock_get_config.return_value = mock_config
        
        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {"_id": "123", "name": "updated"}
        mock_get_mongo.return_value = mock_mongo
        
        breadcrumb = {
            "from_ip": "192.168.1.1",
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "correlation_id": "test-id"
        }
        
        # Act
        result = ControlService.update_control("123", {"name": "updated"}, self.mock_token, breadcrumb)
        
        # Assert
        self.assertIsNotNone(result)
        call_args = mock_mongo.update_document.call_args
        set_data = call_args[1]["set_data"]
        # Verify breadcrumb is used directly without transformation
        self.assertEqual(set_data["saved"], breadcrumb)
        self.assertEqual(set_data["saved"]["from_ip"], "192.168.1.1")
    
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
        
        mock_collection = MagicMock()
        mock_collection.find.side_effect = Exception("Database error")
        
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
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
