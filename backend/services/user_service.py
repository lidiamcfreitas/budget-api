from typing import Optional, List, TypeVar
from fastapi import HTTPException, Request
from firebase_admin import auth, firestore
from models import BaseAuditModel, User
from .base_service import BaseService, ServiceException
from utils import get_token, maybe_throw_not_found, handle_exceptions

T = TypeVar("T", bound=BaseAuditModel)  # Defines a generic type variable


class UserServiceException(ServiceException):
    """Specific exception class for user-related errors."""
    pass


class UserService(BaseService):
    """Service class for handling user-related operations."""
    collection = "users"

    def __init__(self, db: firestore.Client):
        """Initialize the user service."""
        super().__init__()
        self.db = db
        self.logger.info("UserService initialized")

  # @handle_exceptions("Error creating document")
  # Same as in base class but do not exclude id field
    async def create(self, request: Request, doc: T, exclude_id=False) -> T:
        return await super().create(request, doc, exclude_id)

    @handle_exceptions("Error listing users")
    async def list_users(self, skip: int = 0, limit: int = 10, search: Optional[str] = None) -> List[User]:
        users_ref = self.db.collection(self.collection)
        
        if search:
            # Case-insensitive search on name or email
            query = users_ref.where('name', '>=', search)\
                          .where('name', '<=', search + '\uf8ff')\
                          .order_by('name')\
                          .offset(skip)\
                          .limit(limit)
        else:
            query = users_ref.order_by('created_at', direction=firestore.Query.DESCENDING)\
                          .offset(skip)\
                          .limit(limit)
        
        users_snapshot = query.stream()
        return [User.from_dict(doc.to_dict()) for doc in users_snapshot]