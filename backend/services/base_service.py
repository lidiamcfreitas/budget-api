import asyncio
import logging
from typing import Any, Dict, Optional, TypeVar
from functools import wraps
import traceback
from utils import get_token, maybe_throw_not_found
from firebase_admin import firestore, auth
from abc import ABC, abstractmethod
from fastapi import HTTPException, Request
from models import BaseAuditModel


T = TypeVar("T", bound=BaseAuditModel)  # Defines a generic type variable

class ServiceException(Exception):
    """Base exception class for service-related errors."""
    pass

class NotImplementedException(Exception):
    pass

def handle_exceptions(func):
    """Decorator for consistent exception handling in service methods."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ServiceException as e:
            # Re-raise service-specific exceptions
            raise
        except Exception as e:
            # Wrap unknown exceptions
            raise ServiceException(f"Service operation failed: {str(e)}") from e
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ServiceException as e:
            # Re-raise service-specific exceptions
            raise
        except Exception as e:
            # Wrap unknown exceptions
            raise ServiceException(f"Service operation failed: {str(e)}") from e
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

class BaseService(ABC):
    """Base service class providing common functionality for all services."""
    
    def __init__(self):
        """Initialize the base service with a logger and firestore."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()
        self.db = firestore.client()
    
    @property
    @abstractmethod
    def collection(self):
        raise NotImplementedException()  # Abstract property, must be implemented by subclasses

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
        class_name = type(self).__name__
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        if context:
            error_details.update(context)
        
        self.logger.error(f"{class_name} error occurred: {error_details}")
    
    @handle_exceptions
    async def verify_user(self, request: Request):
        token = get_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        self.logger.info(f"Decoded user ID: {user_id}")

        return user_id

    @handle_exceptions
    async def create(self, request: Request, collection_class: T) -> T:
        """
        Create a new document of the type T.

        Args:
            collection_class: The class of the document to create

        Returns:
            T object containing the created document information

        Raises:
            ServiceException: If document creation fails
        """
        class_name = type(self).__name__
        self.logger.debug(f"Creating {class_name} with ID: {collection_class.id}")
        await self.verify_user(request)
        try:
            return await self.get_user(collection_class.id)
        except ServiceException:
            user_ref = self.db.collection(self.collection).document(collection_class.id)
            user_ref.set(collection_class.dict())
            return collection_class
        except Exception as e:
            self.log_error(e, {'id': collection_class.id})
            raise

    @handle_exceptions
    async def get(self, request: Request, id: str) -> T:
        """
        Retrieve document information by ID.

        Args:
            id: The unique identifier of the document

        Returns:
            T object containing document information

        Raises:
            ServiceException: If document retrieval fails
        """
        class_name = type(self).__name__
        self.logger.debug(f"Getting {class_name} with ID: {id}")
        await self.verify_user(request)
        try:
            self.logger.debug("Querying Firestore for document")
            doc_ref = self.db.collection(self.collection).document(id).get()
            
            if doc_ref.exists:
                doc_data = doc_ref.to_dict()
                self.logger.debug(f"Found doc data: {doc_data}")
                self.logger.info(f"Successfully retrieved {class_name}: {id}")
                return self.__class__(**doc_data)
            else:
                self.logger.debug(f"No {class_name} found with ID: {id}")
                raise ServiceException(f"{class_name} not found: {id}")
                
        except Exception as e:
            self.log_error(e, {'id': id})
            raise


    @handle_exceptions
    async def update(self, request: Request, id: str, doc_update: T) -> T:
        class_name = type(self).__name__
        self.logger.debug(f"Updating {class_name} with ID: {id}")
        await self.verify_user(request)
        doc_ref = self.db.collection(self.collection).document(id)
        
        # Get current doc data
        doc = doc_ref.get()
        maybe_throw_not_found(doc, f"{class_name} not found")
        
        # Update only provided fields
        update_data = doc_update.dict(exclude_unset=True)
        update_data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        # Update in Firestore
        doc_ref.update(update_data)
        
        # Get and return updated doc
        updated_doc = doc_ref.get()
        return self.__class__(**updated_doc.to_dict())

    @handle_exceptions
    async def delete(self, id: str):
        class_name = type(self).__name__
        self.logger.debug(f"Deleting {class_name} with ID: {id}")
        await self.verify_user(request)

        doc_ref = self.db.collection(self.collection).document(id)
        doc_ref.delete()
