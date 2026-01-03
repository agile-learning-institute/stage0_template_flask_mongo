"""
Grade service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Grade domain.
"""
from py_utils import MongoIO
from py_utils.flask_utils.exceptions import HTTPNotFound, HTTPInternalServerError
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
    
    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.
        
        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'write')
        
        Note: Grade service only requires a valid token (authentication only).
        """
        pass
    
    @staticmethod
    def get_grades(token, breadcrumb):
        """
        Retrieve all grades.
        
        Args:
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            list: List of all grade documents
        """
        try:
            GradeService._check_permission(token, 'read')
            mongo = MongoIO.get_instance()
            grades = mongo.get_documents(GradeService.COLLECTION_NAME)
            logger.info(f"Retrieved {len(grades)} grades for user {token.get('user_id')}")
            return grades
        except Exception as e:
            logger.error(f"Error retrieving grades: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve grades")
    
    @staticmethod
    def get_grade(grade_id, token, breadcrumb):
        """
        Retrieve a specific grade by ID.
        
        Args:
            grade_id: The grade ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The grade document
            
        Raises:
            HTTPNotFound: If grade is not found
        """
        try:
            GradeService._check_permission(token, 'read')
            
            mongo = MongoIO.get_instance()
            grade = mongo.get_document(GradeService.COLLECTION_NAME, grade_id)
            if grade is None:
                raise HTTPNotFound(f"Grade {grade_id} not found")
            
            logger.info(f"Retrieved grade {grade_id} for user {token.get('user_id')}")
            return grade
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving grade {grade_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve grade {grade_id}")

