"""
Unit tests for TestRun service.
"""
import unittest
from unittest.mock import patch, MagicMock
from src.services.testrun_service import TestRunService
from py_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound, HTTPInternalServerError


class TestTestRunService(unittest.TestCase):
    """Test cases for TestRunService."""
    
    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}
    
    @patch('src.services.testrun_service.MongoIO.get_instance')
    def test_create_testrun_success(self, mock_get_instance):
        """Test successful creation of a test run."""
        # Arrange
        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_instance.return_value = mock_mongo
        
        data = {"name": "Test Run 1", "status": "pending"}
        
        # Act
        testrun_id = TestRunService.create_testrun(data, self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertEqual(testrun_id, "123")
        mock_mongo.create_document.assert_called_once_with("TestRun", data)
    
    @patch('src.services.testrun_service.MongoIO.get_instance')
    def test_create_testrun_no_permission(self, mock_get_instance):
        """Test create_testrun raises HTTPForbidden when user lacks admin role."""
        # Arrange
        mock_token_no_permission = {"user_id": "test_user", "roles": ["developer"]}
        
        # Act & Assert
        with self.assertRaises(HTTPForbidden):
            TestRunService.create_testrun({"name": "Test"}, mock_token_no_permission, self.mock_breadcrumb)
    
    @patch('src.services.testrun_service.MongoIO.get_instance')
    def test_get_testruns_success(self, mock_get_instance):
        """Test successful retrieval of all test runs."""
        # Arrange
        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [
            {"_id": "123", "name": "Test Run 1"},
            {"_id": "456", "name": "Test Run 2"}
        ]
        mock_get_instance.return_value = mock_mongo
        
        # Act
        testruns = TestRunService.get_testruns(self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertEqual(len(testruns), 2)
        mock_mongo.get_documents.assert_called_once_with("TestRun")
    
    @patch('src.services.testrun_service.MongoIO.get_instance')
    def test_get_testrun_success(self, mock_get_instance):
        """Test successful retrieval of a specific test run."""
        # Arrange
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": "123", "name": "Test Run 1"}
        mock_get_instance.return_value = mock_mongo
        
        # Act
        testrun = TestRunService.get_testrun("123", self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertIsNotNone(testrun)
        self.assertEqual(testrun["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("TestRun", "123")
    
    @patch('src.services.testrun_service.MongoIO.get_instance')
    def test_update_testrun_success(self, mock_get_instance):
        """Test successful update of a test run."""
        # Arrange
        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {"_id": "123", "name": "Updated Test Run"}
        mock_get_instance.return_value = mock_mongo
        
        data = {"name": "Updated Test Run"}
        
        # Act
        updated = TestRunService.update_testrun("123", data, self.mock_token, self.mock_breadcrumb)
        
        # Assert
        self.assertIsNotNone(updated)
        self.assertEqual(updated["name"], "Updated Test Run")
        mock_mongo.update_document.assert_called_once()
        call_args = mock_mongo.update_document.call_args
        self.assertEqual(call_args[1]["document_id"], "123")
        self.assertEqual(call_args[1]["set_data"]["name"], "Updated Test Run")
    
    @patch('src.services.testrun_service.MongoIO.get_instance')
    def test_update_testrun_prevent_id_update(self, mock_get_instance):
        """Test update_testrun raises HTTPForbidden when trying to update _id."""
        # Arrange
        data = {"_id": "999", "name": "Updated"}
        
        # Act & Assert
        with self.assertRaises(HTTPForbidden) as context:
            TestRunService.update_testrun("123", data, self.mock_token, self.mock_breadcrumb)
        
        self.assertIn("_id", str(context.exception))
    
    @patch('src.services.testrun_service.MongoIO.get_instance')
    def test_update_testrun_no_permission(self, mock_get_instance):
        """Test update_testrun raises HTTPForbidden when user lacks admin role."""
        # Arrange
        mock_token_no_permission = {"user_id": "test_user", "roles": ["developer"]}
        
        # Act & Assert
        with self.assertRaises(HTTPForbidden):
            TestRunService.update_testrun("123", {"name": "Updated"}, mock_token_no_permission, self.mock_breadcrumb)
    
    @patch('src.services.testrun_service.MongoIO.get_instance')
    def test_update_testrun_not_found(self, mock_get_instance):
        """Test update_testrun raises HTTPNotFound when test run not found."""
        # Arrange
        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = None
        mock_get_instance.return_value = mock_mongo
        
        # Act & Assert
        with self.assertRaises(HTTPNotFound) as context:
            TestRunService.update_testrun("999", {"name": "Updated"}, self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))


if __name__ == '__main__':
    unittest.main()

