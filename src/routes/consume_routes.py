"""
Consume routes for Flask API.

Provides endpoints for Consume domain:
- GET /api/consume - Get all consume documents
- GET /api/consume/<id> - Get a specific consume document by ID
"""
from flask import Blueprint, jsonify, request
from py_utils.flask_utils.token import create_flask_token
from py_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from py_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.consume_service import ConsumeService

import logging
logger = logging.getLogger(__name__)


def create_consume_routes():
    """
    Create a Flask Blueprint exposing consume endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with consume routes
    """
    consume_routes = Blueprint('consume_routes', __name__)
    
    @consume_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_consumes():
        """
        GET /api/consume - Retrieve all consume documents.
        
        Returns:
            JSON response with list of consume documents
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        consumes = ConsumeService.get_consumes(token, breadcrumb)
        logger.info(f"get_consumes Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(consumes), 200
    
    @consume_routes.route('/<consume_id>', methods=['GET'])
    @handle_route_exceptions
    def get_consume(consume_id):
        """
        GET /api/consume/<id> - Retrieve a specific consume document by ID.
        
        Args:
            consume_id: The consume ID to retrieve
            
        Returns:
            JSON response with the consume document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        consume = ConsumeService.get_consume(consume_id, token, breadcrumb)
        logger.info(f"get_consume Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(consume), 200
    
    logger.info("Consume Flask Routes Registered")
    return consume_routes
