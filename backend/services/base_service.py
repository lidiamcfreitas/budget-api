import asyncio
import logging
from typing import Any, Dict, Optional, TypeVar
from functools import wraps
import traceback
from utils import get_token, maybe_throw_not_found, handle_exceptions
from firebase_admin import firestore, auth
from abc import ABC, abstractmethod
from fastapi import HTTPException, Request
from models import BaseAuditModel
from pprint import pformat


T = TypeVar("T", bound=BaseAuditModel)  # Defines a generic type variable

class ServiceException(Exception):
    """Base exception class for service-related errors."""
    pass

class NotImplementedException(Exception):
    pass

class DocNotFoundException(Exception):
    pass

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
        # Only add handler if none exist
        if not self.logger.handlers:
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
        
        self.logger.error(f"{class_name} error occurred: {pformat(error_details)}")

    # @handle_exceptions("Error verifying user")
    async def verify_user(self, request: Request):
        token = get_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        self.logger.info(f"Decoded user ID: {user_id}")

        return user_id

    # @handle_exceptions("Error creating document")
    async def create(self, request: Request, collection_class: T, exclude_id=True) -> T:
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
        try:
            await self.verify_user(request)
            
            # Log the raw collection class data
            self.logger.info(f"Raw collection class data: {pformat(collection_class)}")
            
            # Get dictionary representation excluding id field
            if exclude_id:
                dict_data = collection_class.dict(exclude={'id'})
            else:
                dict_data = collection_class.dict()
            self.logger.info(f"Dictionary representation: {pformat(dict_data)}")
            
            # Create the document directly
            self.logger.info("Creating new document")
            created_doc = collection_class.create(self.db, self.collection, exclude_id, **dict_data)
            
            self.logger.debug(f"Successfully created {class_name}")
            return created_doc
        except Exception as e:
            self.log_error(e)
            raise

    # @handle_exceptions("Error getting document")
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
        try:
            await self.verify_user(request)
            self.logger.debug("Querying Firestore for document")
            doc_ref = self.db.collection(self.collection).document(id).get()
            
            if doc_ref.exists:
                doc_data = doc_ref.to_dict()
                self.logger.debug(f"Found doc data: {doc_data}")
                self.logger.info(f"Successfully retrieved {class_name}: {id}")
                return self.__class__(**doc_data)
            else:
                self.logger.debug(f"No {class_name} found with ID: {id}")
                raise DocNotFoundException(f"{class_name} not found: {id}")
                
        except DocNotFoundException:
            # This is an expected case, just re-raise without error logging
            raise
        except Exception as e:
            self.log_error(e, {'id': id})
            raise


    # @handle_exceptions("Error updating document")
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

    # @handle_exceptions("Error deleting document")
    async def delete(self, request: Request, id: str):
        class_name = type(self).__name__
        self.logger.debug(f"Deleting {class_name} with ID: {id}")
        await self.verify_user(request)

        doc_ref = self.db.collection(self.collection).document(id)
        doc_ref.delete()
