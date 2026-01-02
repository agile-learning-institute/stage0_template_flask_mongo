"""
Grade service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Grade domain.
"""
from py_utils import MongoIO
from py_utils.flask_utils.exceptions import HTTPForbidden, HTTPInternalServerError
import logging

logger = logging.getLogger(__name__)


class GradeService:
    """
    Service class for Grade domain operations.
    
    Handles:
    - RBAC authorization checks
    - MongoDB operations via MongoIO singleton
    - Business logic for Grade domain
    """
    
    COLLECTION_NAME = "Grade"
    
    def __init__(self):
        """Initialize the GradeService."""
        self.mongo = MongoIO.get_instance()
    
    def _check_permission(self, token, operation):
        """
        Check if the user has permission to perform an operation.
        
        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'write')
            
        Raises:
            HTTPForbidden: If user doesn't have required permission
        """
        roles = token.get('roles', [])
        # Simple RBAC: allow read operations for any authenticated user
        # In production, implement more sophisticated role-based checks
        if operation == 'read' and not roles:
            raise HTTPForbidden("Insufficient permissions to read grades")
    
    def get_grades(self, token, breadcrumb):
        """
        Retrieve all grades.
        
        Args:
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            list: List of all grade documents
        """
        try:
            self._check_permission(token, 'read')
            
            grades = self.mongo.get_documents(self.COLLECTION_NAME)
            logger.info(f"Retrieved {len(grades)} grades for user {token.get('user_id')}")
            return grades
        except HTTPForbidden:
            raise
        except Exception as e:
            logger.error(f"Error retrieving grades: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve grades")
    
    def get_grade(self, grade_id, token, breadcrumb):
        """
        Retrieve a specific grade by ID.
        
        Args:
            grade_id: The grade ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict or None: The grade document if found, None otherwise
        """
        try:
            self._check_permission(token, 'read')
            
            grade = self.mongo.get_document(self.COLLECTION_NAME, grade_id)
            if grade:
                logger.info(f"Retrieved grade {grade_id} for user {token.get('user_id')}")
            else:
                logger.info(f"Grade {grade_id} not found for user {token.get('user_id')}")
            return grade
        except HTTPForbidden:
            raise
        except Exception as e:
            logger.error(f"Error retrieving grade {grade_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve grade {grade_id}")

