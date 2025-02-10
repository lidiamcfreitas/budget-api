from typing import Optional, List
from fastapi import HTTPException, Request
from firebase_admin import auth, firestore
from models import User
from .base_service import BaseService, ServiceException
from utils import get_token, maybe_throw_not_found

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

    @BaseService.handle_exceptions
    async def create_user(self, user: User) -> User:
        """
        Create a new user account.

        Args:
            user: User model containing user information including email and password

        Returns:
            User object containing the created user information

        Raises:
            UserServiceException: If user creation fails
        """
        self.logger.debug(f"Creating user with ID: {user.id}")
        try:
            return await self.get_user(user.id)
        except UserServiceException:
            user_ref = self.db.collection(self.collection).document(user.id)
            user_ref.set(user.dict())
            return user
        except Exception as e:
            self.log_error(e, {'user_id': user.user_id})
            raise

    @BaseService.handle_exceptions
    async def get_user(self, user_id: str) -> User:
        """
        Retrieve user information by ID.

        Args:
            user_id: The unique identifier of the user

        Returns:
            User object containing user information

        Raises:
            UserServiceException: If user retrieval fails
        """
        self.logger.debug(f"Getting user with ID: {user_id}")
        try:
            self.logger.debug("Querying Firestore for user document")
            user_ref = self.db.collection(self.collection).document(user_id).get()
            
            if user_ref.exists:
                user_data = user_ref.to_dict()
                self.logger.debug(f"Found user data: {user_data}")
                self.logger.info(f"Successfully retrieved user: {user_id}")
                return User(**user_data)
            else:
                self.logger.debug(f"No user found with ID: {user_id}")
                raise UserServiceException(f"User not found: {user_id}")
                
        except Exception as e:
            self.log_error(e, {'user_id': user_id})
            raise

    @BaseService.handle_exceptions
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

    @BaseService.handle_exceptions
    async def update_user(self, user_id: str, user_update: User) -> User:
        user_ref = self.db.collection(self.collection).document(user_id)
        
        # Get current user data
        user_doc = user_ref.get()
        maybe_throw_not_found(user_doc, "User not found")
        
        # Update only provided fields
        update_data = user_update.dict(exclude_unset=True)
        update_data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        # Update in Firestore
        user_ref.update(update_data)
        
        # Get and return updated user
        updated_user_doc = user_ref.get()
        return User(**updated_user_doc.to_dict())

    @BaseService.handle_exceptions
    async def delete_user(self, user_id: str):
        user_ref = self.db.collection('users').document(user_id)
        
        # Delete associated data (budgets, transactions, etc.)
        # This should be done in a transaction or batch
        batch = self.db.batch()
        
        # Delete user's budgets
        budgets = self.db.collection('budgets').where('user_id', '==', user_id).stream()
        for budget in budgets:
            batch.delete(budget.reference)
        
        # Delete the user document
        batch.delete(user_ref)
        
        # Commit the batch
        batch.commit()

    @BaseService.handle_exceptions
    def verify_user(self, request: Request):
        token = get_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        self.logger.info(f"Decoded user ID: {user_id}")

        return user_id