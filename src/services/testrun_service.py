"""
TestRun service for business logic and RBAC.

Handles RBAC checks, security validations, and MongoDB operations for TestRun domain.
"""
from py_utils import MongoIO
from py_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound, HTTPInternalServerError
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
    
    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.
        
        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'create', 'update')
            
        Raises:
            HTTPForbidden: If user doesn't have required permission
        """
        roles = token.get('roles', [])
        # Read: any authenticated token can read
        # Write operations (create, update): require 'admin' role
        if operation in ['create', 'update']:
            if 'admin' not in roles:
                raise HTTPForbidden(f"Insufficient permissions to {operation} test runs")
    
    @staticmethod
    def _validate_update_data(data):
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
    
    @staticmethod
    def create_testrun(data, token, breadcrumb):
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
            TestRunService._check_permission(token, 'create')
            
            # Remove _id if present (MongoDB will generate it)
            if '_id' in data:
                del data['_id']
            
            mongo = MongoIO.get_instance()
            testrun_id = mongo.create_document(TestRunService.COLLECTION_NAME, data)
            logger.info(f"Created test run {testrun_id} for user {token.get('user_id')}")
            return testrun_id
        except HTTPForbidden:
            raise
        except Exception as e:
            logger.error(f"Error creating test run: {str(e)}")
            raise HTTPInternalServerError("Failed to create test run")
    
    @staticmethod
    def get_testruns(token, breadcrumb):
        """
        Retrieve all test runs.
        
        Args:
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            list: List of all test run documents
        """
        try:
            TestRunService._check_permission(token, 'read')
            mongo = MongoIO.get_instance()
            testruns = mongo.get_documents(TestRunService.COLLECTION_NAME)
            logger.info(f"Retrieved {len(testruns)} test runs for user {token.get('user_id')}")
            return testruns
        except Exception as e:
            logger.error(f"Error retrieving test runs: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve test runs")
    
    @staticmethod
    def get_testrun(testrun_id, token, breadcrumb):
        """
        Retrieve a specific test run by ID.
        
        Args:
            testrun_id: The test run ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The test run document
            
        Raises:
            HTTPNotFound: If test run is not found
        """
        try:
            TestRunService._check_permission(token, 'read')
            
            mongo = MongoIO.get_instance()
            testrun = mongo.get_document(TestRunService.COLLECTION_NAME, testrun_id)
            if testrun is None:
                raise HTTPNotFound(f"Test run {testrun_id} not found")
            
            logger.info(f"Retrieved test run {testrun_id} for user {token.get('user_id')}")
            return testrun
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error retrieving test run {testrun_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve test run {testrun_id}")
    
    @staticmethod
    def update_testrun(testrun_id, data, token, breadcrumb):
        """
        Update a test run.
        
        Args:
            testrun_id: The test run ID to update
            data: Dictionary containing fields to update
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The updated test run document
            
        Raises:
            HTTPNotFound: If test run is not found
        """
        try:
            TestRunService._check_permission(token, 'update')
            TestRunService._validate_update_data(data)
            
            # Build update data with $set operator
            set_data = {k: v for k, v in data.items() if k != '_id'}
            
            mongo = MongoIO.get_instance()
            updated = mongo.update_document(
                TestRunService.COLLECTION_NAME,
                document_id=testrun_id,
                set_data=set_data
            )
            
            if updated is None:
                raise HTTPNotFound(f"Test run {testrun_id} not found")
            
            logger.info(f"Updated test run {testrun_id} for user {token.get('user_id')}")
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating test run {testrun_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update test run {testrun_id}")

