"""
TestRun service for business logic and RBAC.

Handles RBAC checks, security validations, and MongoDB operations for TestRun domain.
"""
from py_utils import MongoIO
from py_utils.flask_utils.exceptions import HTTPForbidden, HTTPInternalServerError
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class TestRunService:
    """
    Service class for TestRun domain operations.
    
    Handles:
    - RBAC authorization checks
    - Security checks (prevent _id updates)
    - MongoDB operations via MongoIO singleton
    - Business logic for TestRun domain
    """
    
    COLLECTION_NAME = "TestRun"
    
    def __init__(self):
        """Initialize the TestRunService."""
        self.mongo = MongoIO.get_instance()
    
    def _check_permission(self, token, operation):
        """
        Check if the user has permission to perform an operation.
        
        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'write', 'create', 'update')
            
        Raises:
            HTTPForbidden: If user doesn't have required permission
        """
        roles = token.get('roles', [])
        # Simple RBAC: allow read for any authenticated user, write requires admin or developer
        if operation == 'read' and not roles:
            raise HTTPForbidden("Insufficient permissions to read test runs")
        if operation in ['write', 'create', 'update']:
            if 'admin' not in roles and 'developer' not in roles:
                raise HTTPForbidden(f"Insufficient permissions to {operation} test runs")
    
    def _validate_update_data(self, data):
        """
        Validate update data to prevent security issues.
        
        Args:
            data: Dictionary of fields to update
            
        Raises:
            HTTPForbidden: If update data contains _id or other restricted fields
        """
        # Prevent updates to _id
        if '_id' in data:
            raise HTTPForbidden("Cannot update _id field")
        
        # Additional security checks can be added here
        # For example, prevent updates to certain system fields
    
    def create_testrun(self, data, token, breadcrumb):
        """
        Create a new test run.
        
        Args:
            data: Dictionary containing test run data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            str: The ID of the created test run
        """
        try:
            self._check_permission(token, 'create')
            
            # Remove _id if present (MongoDB will generate it)
            if '_id' in data:
                del data['_id']
            
            testrun_id = self.mongo.create_document(self.COLLECTION_NAME, data)
            logger.info(f"Created test run {testrun_id} for user {token.get('user_id')}")
            return testrun_id
        except HTTPForbidden:
            raise
        except Exception as e:
            logger.error(f"Error creating test run: {str(e)}")
            raise HTTPInternalServerError("Failed to create test run")
    
    def get_testruns(self, token, breadcrumb):
        """
        Retrieve all test runs.
        
        Args:
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            list: List of all test run documents
        """
        try:
            self._check_permission(token, 'read')
            
            testruns = self.mongo.get_documents(self.COLLECTION_NAME)
            logger.info(f"Retrieved {len(testruns)} test runs for user {token.get('user_id')}")
            return testruns
        except HTTPForbidden:
            raise
        except Exception as e:
            logger.error(f"Error retrieving test runs: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve test runs")
    
    def get_testrun(self, testrun_id, token, breadcrumb):
        """
        Retrieve a specific test run by ID.
        
        Args:
            testrun_id: The test run ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict or None: The test run document if found, None otherwise
        """
        try:
            self._check_permission(token, 'read')
            
            testrun = self.mongo.get_document(self.COLLECTION_NAME, testrun_id)
            if testrun:
                logger.info(f"Retrieved test run {testrun_id} for user {token.get('user_id')}")
            else:
                logger.info(f"Test run {testrun_id} not found for user {token.get('user_id')}")
            return testrun
        except HTTPForbidden:
            raise
        except Exception as e:
            logger.error(f"Error retrieving test run {testrun_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve test run {testrun_id}")
    
    def update_testrun(self, testrun_id, data, token, breadcrumb):
        """
        Update a test run.
        
        Args:
            testrun_id: The test run ID to update
            data: Dictionary containing fields to update
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict or None: The updated test run document if found, None otherwise
        """
        try:
            self._check_permission(token, 'update')
            self._validate_update_data(data)
            
            # Build update data with $set operator
            set_data = {k: v for k, v in data.items() if k != '_id'}
            
            updated = self.mongo.update_document(
                self.COLLECTION_NAME,
                document_id=testrun_id,
                set_data=set_data
            )
            
            if updated:
                logger.info(f"Updated test run {testrun_id} for user {token.get('user_id')}")
            else:
                logger.info(f"Test run {testrun_id} not found for update by user {token.get('user_id')}")
            
            return updated
        except HTTPForbidden:
            raise
        except Exception as e:
            logger.error(f"Error updating test run {testrun_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update test run {testrun_id}")

