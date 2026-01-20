"""
Control routes for Flask API.

Provides endpoints for Control domain:
- POST /api/control - Create a new control document
- GET /api/control - Get all control documents (with optional ?name= query parameter)
- GET /api/control/<id> - Get a specific control document by ID
- PATCH /api/control/<id> - Update a control document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.control_service import ControlService

import logging
logger = logging.getLogger(__name__)


def create_control_routes():
    """
    Create a Flask Blueprint exposing control endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with control routes
    """
    control_routes = Blueprint('control_routes', __name__)
    
    @control_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_control():
        """
        POST /api/control - Create a new control document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created control document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        control_id = ControlService.create_control(data, token, breadcrumb)
        control = ControlService.get_control(control_id, token, breadcrumb)
        
        logger.info(f"create_control Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(control), 201
    
    @control_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_controls():
        """
        GET /api/control - Retrieve all control documents.
        
        Query Parameters:
            name: Optional name filter for partial matching (case-insensitive)
        
        Returns:
            JSON response with list of control documents
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        # Get optional name query parameter
        name = request.args.get('name')
        
        controls = ControlService.get_controls(token, breadcrumb, name=name)
        logger.info(f"get_controls Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(controls), 200
    
    @control_routes.route('/<control_id>', methods=['GET'])
    @handle_route_exceptions
    def get_control(control_id):
        """
        GET /api/control/<id> - Retrieve a specific control document by ID.
        
        Args:
            control_id: The control ID to retrieve
            
        Returns:
            JSON response with the control document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        control = ControlService.get_control(control_id, token, breadcrumb)
        logger.info(f"get_control Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(control), 200
    
    @control_routes.route('/<control_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_control(control_id):
        """
        PATCH /api/control/<id> - Update a control document.
        
        Args:
            control_id: The control ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated control document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        control = ControlService.update_control(control_id, data, token, breadcrumb)
        
        logger.info(f"update_control Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(control), 200
    
    logger.info("Control Flask Routes Registered")
    return control_routes
