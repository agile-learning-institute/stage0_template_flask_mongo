"""
Create routes for Flask API.

Provides endpoints for Create domain:
- POST /api/create - Create a new create document
- GET /api/create - Get all create documents
- GET /api/create/<id> - Get a specific create document by ID
"""
from flask import Blueprint, jsonify, request
from py_utils.flask_utils.token import create_flask_token
from py_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from py_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.create_service import CreateService

import logging
logger = logging.getLogger(__name__)


def create_create_routes():
    """
    Create a Flask Blueprint exposing create endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with create routes
    """
    create_routes = Blueprint('create_routes', __name__)
    
    @create_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_create():
        """
        POST /api/create - Create a new create document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created create document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        create_id = CreateService.create_create(data, token, breadcrumb)
        create = CreateService.get_create(create_id, token, breadcrumb)
        
        logger.info(f"create_create Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(create), 201
    
    @create_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_creates():
        """
        GET /api/create - Retrieve all create documents.
        
        Returns:
            JSON response with list of create documents
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        creates = CreateService.get_creates(token, breadcrumb)
        logger.info(f"get_creates Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(creates), 200
    
    @create_routes.route('/<create_id>', methods=['GET'])
    @handle_route_exceptions
    def get_create(create_id):
        """
        GET /api/create/<id> - Retrieve a specific create document by ID.
        
        Args:
            create_id: The create ID to retrieve
            
        Returns:
            JSON response with the create document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        create = CreateService.get_create(create_id, token, breadcrumb)
        logger.info(f"get_create Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(create), 200
    
    logger.info("Create Flask Routes Registered")
    return create_routes
