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
        
        Example RBAC implementation:
            if operation == 'read':
                # Read requires any authenticated user (no additional check needed)
                # For stricter requirements, you could require specific roles:
                # if not any(role in token.get('roles', []) for role in ['staff', 'admin', 'viewer']):
                #     raise HTTPForbidden("Insufficient permissions to read consume documents")
                pass
        """
        pass
    
    @staticmethod
    def get_consumes(token, breadcrumb, name=None):
        """
        Retrieve all consume documents, optionally filtered by name.
        
        Args:
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            name: Optional name filter (supports partial matches)
            
        Returns:
            list: List of consume documents matching the criteria
        """
        try:
            ConsumeService._check_permission(token, 'read')
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            
            if name:
                # Use regex for partial matching (case-insensitive)
                query = {"name": {"$regex": name, "$options": "i"}}
                consumes = mongo.get_documents(config.CONSUME_COLLECTION_NAME, match=query)
                logger.info(f"Retrieved {len(consumes)} consumes matching name '{name}' for user {token.get('user_id')}")
            else:
                consumes = mongo.get_documents(config.CONSUME_COLLECTION_NAME)
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
            config = Config.get_instance()
            consume = mongo.get_document(config.CONSUME_COLLECTION_NAME, consume_id)
            if consume is None:
                raise HTTPNotFound(f"Consume {consume_id} not found")
            
            logger.info(f"Retrieved consume {consume_id} for user {token.get('user_id')}")
            return consume
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving consume {consume_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve consume {consume_id}")
