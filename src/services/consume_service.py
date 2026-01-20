"""
Consume service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Consume domain.
"""
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound, HTTPInternalServerError
import logging

logger = logging.getLogger(__name__)


class ConsumeService:
    """
    Service class for Consume domain operations.
    
    Handles:
    - RBAC authorization checks (placeholder for future implementation)
    - MongoDB operations via MongoIO singleton
    - Business logic for Consume domain (read-only)
    """
    
    @staticmethod
    def _get_collection_name():
        """Get the Consume collection name from config."""
        config = Config.get_instance()
        return config.CONSUME_COLLECTION_NAME
    
    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.
        
        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read')
        
        Raises:
            HTTPForbidden: If user doesn't have required permission
            
        Note: This is a placeholder for future RBAC implementation.
        For now, all operations require a valid token (authentication only).
        """
        pass
    
    @staticmethod
    def get_consumes(token, breadcrumb):
        """
        Retrieve all consume documents.
        
        Args:
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            list: List of all consume documents
        """
        try:
            ConsumeService._check_permission(token, 'read')
            mongo = MongoIO.get_instance()
            consumes = mongo.get_documents(ConsumeService._get_collection_name())
            logger.info(f"Retrieved {len(consumes)} consumes for user {token.get('user_id')}")
            return consumes
        except Exception as e:
            logger.error(f"Error retrieving consumes: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve consumes")
    
    @staticmethod
    def get_consume(consume_id, token, breadcrumb):
        """
        Retrieve a specific consume document by ID.
        
        Args:
            consume_id: The consume ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The consume document
            
        Raises:
            HTTPNotFound: If consume is not found
        """
        try:
            ConsumeService._check_permission(token, 'read')
            
            mongo = MongoIO.get_instance()
            consume = mongo.get_document(ConsumeService._get_collection_name(), consume_id)
            if consume is None:
                raise HTTPNotFound(f"Consume {consume_id} not found")
            
            logger.info(f"Retrieved consume {consume_id} for user {token.get('user_id')}")
            return consume
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving consume {consume_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve consume {consume_id}")
