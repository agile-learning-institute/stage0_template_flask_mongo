"""
Control service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Control domain.
"""
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPNotFound, HTTPInternalServerError
from bson import ObjectId
from bson.errors import InvalidId
import logging

logger = logging.getLogger(__name__)


class ControlService:
    """
    Service class for Control domain operations.
    
    Handles:
    - RBAC authorization checks (placeholder for future implementation)
    - MongoDB operations via MongoIO singleton
    - Business logic for Control domain
    """
    
    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.
        
        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'create', 'update')
        
        Raises:
            HTTPForbidden: If user doesn't have required permission
            
        Note: This is a placeholder for future RBAC implementation.
        For now, all operations require a valid token (authentication only).
        """
        pass
    
    @staticmethod
    def _validate_update_data(data):
        """
        Validate update data to prevent security issues.
        
        Args:
            data: Dictionary of fields to update
            
        Raises:
            HTTPForbidden: If update data contains restricted fields
        """
        # Prevent updates to _id and system-managed fields
        restricted_fields = ['_id', 'created', 'saved']
        for field in restricted_fields:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")
    
    @staticmethod
    def create_control(data, token, breadcrumb):
        """
        Create a new control document.
        
        Args:
            data: Dictionary containing control data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging (contains at_time, by_user, from_ip, correlation_id)
            
        Returns:
            str: The ID of the created control document
        """
        try:
            ControlService._check_permission(token, 'create')
            
            # Remove _id if present (MongoDB will generate it)
            if '_id' in data:
                del data['_id']
            
            # Build breadcrumb object for created/saved fields (schema expects Registry, not from_ip)
            # Provide default IP if from_ip is None or empty (can happen with Docker/reverse proxies)
            from_ip = breadcrumb.get('from_ip') or '127.0.0.1'
            breadcrumb_obj = {
                "Registry": from_ip,
                "at_time": breadcrumb.get('at_time'),
                "by_user": breadcrumb.get('by_user'),
                "correlation_id": breadcrumb.get('correlation_id')
            }
            
            # Automatically populate required fields: created and saved
            # These are system-managed and should not be provided by the client
            data['created'] = breadcrumb_obj
            data['saved'] = breadcrumb_obj
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            control_id = mongo.create_document(config.CONTROL_COLLECTION_NAME, data)
            logger.info(f"Created control {control_id} for user {token.get('user_id')}")
            return control_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating control: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create control: {error_msg}")
    
    @staticmethod
    def get_controls(token, breadcrumb, name=None):
        """
        Retrieve all control documents, optionally filtered by name.
        
        Args:
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            name: Optional name filter (supports partial matches)
            
        Returns:
            list: List of control documents matching the criteria
        """
        try:
            ControlService._check_permission(token, 'read')
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            
            if name:
                # Use regex for partial matching (case-insensitive)
                query = {"name": {"$regex": name, "$options": "i"}}
                controls = mongo.find_documents(config.CONTROL_COLLECTION_NAME, query)
                logger.info(f"Retrieved {len(controls)} controls matching name '{name}' for user {token.get('user_id')}")
            else:
                controls = mongo.get_documents(config.CONTROL_COLLECTION_NAME)
                logger.info(f"Retrieved {len(controls)} controls for user {token.get('user_id')}")
            
            return controls
        except Exception as e:
            logger.error(f"Error retrieving controls: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve controls")
    
    @staticmethod
    def get_control(control_id, token, breadcrumb):
        """
        Retrieve a specific control document by ID.
        
        Args:
            control_id: The control ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The control document
            
        Raises:
            HTTPNotFound: If control is not found
        """
        try:
            ControlService._check_permission(token, 'read')
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            control = mongo.get_document(config.CONTROL_COLLECTION_NAME, control_id)
            if control is None:
                raise HTTPNotFound(f"Control {control_id} not found")
            
            logger.info(f"Retrieved control {control_id} for user {token.get('user_id')}")
            return control
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving control {control_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve control {control_id}")
    
    @staticmethod
    def update_control(control_id, data, token, breadcrumb):
        """
        Update a control document.
        
        Args:
            control_id: The control ID to update
            data: Dictionary containing fields to update
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The updated control document
            
        Raises:
            HTTPNotFound: If control is not found
        """
        try:
            ControlService._check_permission(token, 'update')
            ControlService._validate_update_data(data)
            
            # Build update data with $set operator (excluding restricted fields)
            restricted_fields = ['_id', 'created', 'saved']
            set_data = {k: v for k, v in data.items() if k not in restricted_fields}
            
            # Automatically update the 'saved' field with current breadcrumb (system-managed)
            # Provide default IP if from_ip is None or empty (can happen with Docker/reverse proxies)
            from_ip = breadcrumb.get('from_ip') or '127.0.0.1'
            breadcrumb_obj = {
                "Registry": from_ip,
                "at_time": breadcrumb.get('at_time'),
                "by_user": breadcrumb.get('by_user'),
                "correlation_id": breadcrumb.get('correlation_id')
            }
            set_data['saved'] = breadcrumb_obj
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated = mongo.update_document(
                config.CONTROL_COLLECTION_NAME,
                document_id=control_id,
                set_data=set_data
            )
            
            if updated is None:
                raise HTTPNotFound(f"Control {control_id} not found")
            
            logger.info(f"Updated control {control_id} for user {token.get('user_id')}")
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating control {control_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update control {control_id}")
