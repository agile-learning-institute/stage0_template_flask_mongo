"""
Consume service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Consume domain.
"""
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPInternalServerError
from bson import ObjectId
from bson.errors import InvalidId
import logging

logger = logging.getLogger(__name__)

# Allowed sort fields for Consume domain
ALLOWED_SORT_FIELDS = ['name', 'description']


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
    def get_consumes(token, breadcrumb, name=None, after_id=None, limit=10, sort_by='name', order='asc'):
        """
        Get infinite scroll batch of sorted, filtered consume documents.
        
        Args:
            token: Authentication token
            breadcrumb: Audit breadcrumb
            name: Optional name filter (simple search)
            after_id: Cursor (ID of last item from previous batch, None for first request)
            limit: Items per batch
            sort_by: Field to sort by
            order: Sort order ('asc' or 'desc')
        
        Returns:
            dict: {
                'items': [...],
                'limit': int,
                'has_more': bool,
                'next_cursor': str|None  # ID of last item, or None if no more
            }
        
        Raises:
            HTTPBadRequest: If invalid parameters provided
        """
        try:
            ConsumeService._check_permission(token, 'read')
            
            # Validate inputs - raise exceptions for invalid values
            if limit < 1:
                raise HTTPBadRequest("limit must be >= 1")
            if limit > 100:
                raise HTTPBadRequest("limit must be <= 100")
            if sort_by not in ALLOWED_SORT_FIELDS:
                raise HTTPBadRequest(f"sort_by must be one of: {', '.join(ALLOWED_SORT_FIELDS)}")
            if order not in ['asc', 'desc']:
                raise HTTPBadRequest("order must be 'asc' or 'desc'")
            
            # Validate after_id format if provided
            if after_id:
                try:
                    ObjectId(after_id)
                except (InvalidId, TypeError):
                    raise HTTPBadRequest("after_id must be a valid MongoDB ObjectId")
            
            # Build filter query
            filter_query = {}
            
            # Simple name search (minimal - can be extended later)
            if name:
                filter_query['name'] = {'$regex': name, '$options': 'i'}
            
            # Add cursor filter if provided (for infinite scroll)
            if after_id:
                # For ascending order: get items with _id > after_id
                # For descending order: get items with _id < after_id
                if order == 'asc':
                    filter_query['_id'] = {'$gt': ObjectId(after_id)}
                else:
                    filter_query['_id'] = {'$lt': ObjectId(after_id)}
            
            # Build sort query
            sort_direction = 1 if order == 'asc' else -1
            sort_query = [(sort_by, sort_direction)]
            
            # Get collection and execute query
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection = mongo.get_collection(config.CONSUME_COLLECTION_NAME)
            
            # Execute query - fetch one extra to check if there are more items
            cursor = collection.find(filter_query).sort(sort_query).limit(limit + 1)
            items = list(cursor)
            
            # Check if there are more items
            has_more = len(items) > limit
            if has_more:
                items = items[:limit]  # Remove the extra item
                next_cursor = str(items[-1]['_id'])  # ID of last item
            else:
                next_cursor = None
            
            logger.info(f"Retrieved {len(items)} consumes (has_more={has_more}) for user {token.get('user_id')}")
            
            return {
                'items': items,
                'limit': limit,
                'has_more': has_more,
                'next_cursor': next_cursor
            }
        except HTTPBadRequest:
            raise
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
