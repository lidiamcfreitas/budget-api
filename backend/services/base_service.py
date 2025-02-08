import logging
from typing import Any, Dict, Optional
from functools import wraps
import traceback
from firebase_admin import firestore


class ServiceException(Exception):
    """Base exception class for service-related errors."""
    pass

class BaseService:
    """Base service class providing common functionality for all services."""
    
    def __init__(self):
        """Initialize the base service with a logger and firestore."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging for the service."""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error with optional context.
        
        Args:
            error: The exception that occurred
            context: Optional dictionary with additional context
        """
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        if context:
            error_details.update(context)
        
        self.logger.error(f"Service error occurred: {error_details}")
    
    @staticmethod
    def handle_exceptions(func):
        """Decorator for consistent exception handling in service methods."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ServiceException as e:
                # Re-raise service-specific exceptions
                raise
            except Exception as e:
                # Wrap unknown exceptions
                raise ServiceException(f"Service operation failed: {str(e)}") from e
        return wrapper

