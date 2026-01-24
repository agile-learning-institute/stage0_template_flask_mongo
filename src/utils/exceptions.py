"""
Local HTTP exceptions for Phase 1 implementation.

This module contains HTTPBadRequest exception that will be harvested to
api_utils.flask_utils.exceptions in Phase 3 after testing is complete.

Phase 1: Local implementation in template_flask_mongo
Phase 3: Extract to api_utils after everything is tested
"""


class HTTPBadRequest(Exception):
    """
    Exception for 400 Bad Request errors.
    
    Raised when request parameters are invalid or malformed.
    
    Phase 1: Local implementation in template_flask_mongo
    Phase 3: Will be moved to api_utils.flask_utils.exceptions
    """
    status_code = 400
    message = "Bad Request"

    def __init__(self, message=None):
        if message:
            self.message = message
        super().__init__(self.message)
