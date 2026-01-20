"""
Create service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Create domain.
"""
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound, HTTPInternalServerError
from bson import ObjectId
from bson.errors import InvalidId
import logging

logger = logging.getLogger(__name__)


class CreateService:
    """
    Service class for Create domain operations.
    
    Handles:
    - RBAC authorization checks (placeholder for future implementation)
    - MongoDB operations via MongoIO singleton
    - Business logic for Create domain
    """
    
    @staticmethod
    def _get_collection_name():
        """Get the Create collection name from config."""
        config = Config.get_instance()
        return config.CREATE_COLLECTION_NAME
    
    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.
        
        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'create')
        
        Raises:
            HTTPForbidden: If user doesn't have required permission
            
        Note: This is a placeholder for future RBAC implementation.
        For now, all operations require a valid token (authentication only).
        """
        pass
    
    @staticmethod
    def create_create(data, token, breadcrumb):
        """
        Create a new create document.
        
        Args:
            data: Dictionary containing create data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging (contains at_time, by_user, from_ip, correlation_id)
            
        Returns:
            str: The ID of the created create document
        """
        try:
            CreateService._check_permission(token, 'create')
            
            # Remove _id if present (MongoDB will generate it)
            if '_id' in data:
                del data['_id']
            
            # Build breadcrumb object for created field (schema expects Registry, not from_ip)
            # Provide default IP if from_ip is None or empty (can happen with Docker/reverse proxies)
            from_ip = breadcrumb.get('from_ip') or '127.0.0.1'
            breadcrumb_obj = {
                "Registry": from_ip,
                "at_time": breadcrumb.get('at_time'),
                "by_user": breadcrumb.get('by_user'),
                "correlation_id": breadcrumb.get('correlation_id')
            }
            
            # Automatically populate required field: created
            # This is system-managed and should not be provided by the client
            data['created'] = breadcrumb_obj
            
            mongo = MongoIO.get_instance()
            create_id = mongo.create_document(CreateService._get_collection_name(), data)
            logger.info(f"Created create {create_id} for user {token.get('user_id')}")
            return create_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating create: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create create: {error_msg}")
    
    @staticmethod
    def get_creates(token, breadcrumb):
        """
        Retrieve all create documents.
        
        Args:
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            list: List of all create documents
        """
        try:
            CreateService._check_permission(token, 'read')
            mongo = MongoIO.get_instance()
            creates = mongo.get_documents(CreateService._get_collection_name())
            logger.info(f"Retrieved {len(creates)} creates for user {token.get('user_id')}")
            return creates
        except Exception as e:
            logger.error(f"Error retrieving creates: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve creates")
    
    @staticmethod
    def get_create(create_id, token, breadcrumb):
        """
        Retrieve a specific create document by ID.
        
        Args:
            create_id: The create ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The create document
            
        Raises:
            HTTPNotFound: If create is not found
        """
        try:
            CreateService._check_permission(token, 'read')
            
            mongo = MongoIO.get_instance()
            create = mongo.get_document(CreateService._get_collection_name(), create_id)
            if create is None:
                raise HTTPNotFound(f"Create {create_id} not found")
            
            logger.info(f"Retrieved create {create_id} for user {token.get('user_id')}")
            return create
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving create {create_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve create {create_id}")
