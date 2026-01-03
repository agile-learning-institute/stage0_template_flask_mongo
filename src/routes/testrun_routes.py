"""
TestRun routes for Flask API.

Provides endpoints for TestRun domain:
- POST /api/testrun - Create a new test run
- GET /api/testrun - Get all test runs
- GET /api/testrun/<id> - Get a specific test run by ID
- PATCH /api/testrun/<id> - Update a test run
"""
from flask import Blueprint, jsonify, request
from py_utils.flask_utils.token import create_flask_token
from py_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from py_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.testrun_service import TestRunService

import logging
logger = logging.getLogger(__name__)


def create_testrun_routes():
    """
    Create a Flask Blueprint exposing testrun endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with testrun routes
    """
    testrun_routes = Blueprint('testrun_routes', __name__)
    
    @testrun_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_testrun():
        """
        POST /api/testrun - Create a new test run.
        
        Request body (JSON):
        {
            "field1": "value1",
            "field2": "value2",
            ...
        }
        
        Returns:
            JSON response with the created test run including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        testrun_id = TestRunService.create_testrun(data, token, breadcrumb)
        testrun = TestRunService.get_testrun(testrun_id, token, breadcrumb)
        
        logger.info(f"create_testrun Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(testrun), 201
    
    @testrun_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_testruns():
        """
        GET /api/testrun - Retrieve all test runs.
        
        Returns:
            JSON response with list of test runs
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        testruns = TestRunService.get_testruns(token, breadcrumb)
        logger.info(f"get_testruns Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(testruns), 200
    
    @testrun_routes.route('/<testrun_id>', methods=['GET'])
    @handle_route_exceptions
    def get_testrun(testrun_id):
        """
        GET /api/testrun/<id> - Retrieve a specific test run by ID.
        
        Args:
            testrun_id: The test run ID to retrieve
            
        Returns:
            JSON response with the test run document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        testrun = TestRunService.get_testrun(testrun_id, token, breadcrumb)
        logger.info(f"get_testrun Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(testrun), 200
    
    @testrun_routes.route('/<testrun_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_testrun(testrun_id):
        """
        PATCH /api/testrun/<id> - Update a test run.
        
        Args:
            testrun_id: The test run ID to update
            
        Request body (JSON):
        {
            "field1": "new_value1",
            "field2": "new_value2",
            ...
        }
        
        Returns:
            JSON response with the updated test run
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        testrun = TestRunService.update_testrun(testrun_id, data, token, breadcrumb)
        
        logger.info(f"update_testrun Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(testrun), 200
    
    logger.info("TestRun Flask Routes Registered")
    return testrun_routes

