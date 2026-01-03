"""
Grade routes for Flask API.

Provides endpoints for Grade domain:
- GET /api/grade - Get all grades
- GET /api/grade/<id> - Get a specific grade by ID
"""
from flask import Blueprint, jsonify, request
from py_utils.flask_utils.token import create_flask_token
from py_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from py_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.grade_service import GradeService

import logging
logger = logging.getLogger(__name__)


def create_grade_routes():
    """
    Create a Flask Blueprint exposing grade endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with grade routes
    """
    grade_routes = Blueprint('grade_routes', __name__)
    
    @grade_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_grades():
        """
        GET /api/grade - Retrieve all grades.
        
        Returns:
            JSON response with list of grades
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        grades = GradeService.get_grades(token, breadcrumb)
        logger.info(f"get_grades Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(grades), 200
    
    @grade_routes.route('/<grade_id>', methods=['GET'])
    @handle_route_exceptions
    def get_grade(grade_id):
        """
        GET /api/grade/<id> - Retrieve a specific grade by ID.
        
        Args:
            grade_id: The grade ID to retrieve
            
        Returns:
            JSON response with the grade document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        grade = GradeService.get_grade(grade_id, token, breadcrumb)
        logger.info(f"get_grade Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(grade), 200
    
    logger.info("Grade Flask Routes Registered")
    return grade_routes

