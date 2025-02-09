from typing import Optional
from firebase_admin import auth, firestore
from models import User
from .base_service import BaseService, ServiceException

class UserServiceException(ServiceException):
    """Specific exception class for user-related errors."""
    pass


class UserService(BaseService):
    """Service class for handling user-related operations."""

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
        self.logger.debug(f"Creating user with ID: {user.user_id}")
        try:
            return await self.get_user(user.user_id)
        except UserServiceException:
            user_ref = self.db.collection("users").document(user.user_id)
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
            user_ref = self.db.collection("users").document(user_id).get()
            
            if user_ref.exists:
                user_data = user_ref.to_dict()
                self.logger.debug(f"Found user data: {user_data}")
                self.logger.info(f"Successfully retrieved user: {user_id}")
                return user_data
            else:
                self.logger.debug(f"No user found with ID: {user_id}")
                raise UserServiceException(f"User not found: {user_id}")
                
        except Exception as e:
            self.log_error(e, {'user_id': user_id})
            raise

    @BaseService.handle_exceptions
    async def update_user(self, user_id: str, user: User) -> User:
        """
        Update user information in both Firebase Auth and Firestore.

        Args:
            user_id: The unique identifier of the user
            user: User model containing fields to update

        Returns:
            User object containing updated user information

        Raises:
            UserServiceException: If user update fails
        """
        self.logger.debug(f"Updating user with ID: {user_id}")
        try:
            if self.get_user(user_id):
                # Update Firebase Auth
                auth_user = auth.update_user(
                    user_id,
                    display_name=user.display_name,
                    photo_url=user.photo_url,
                    email=user.email
                )
                
                # Update Firestore
                updated_user = User(
                    uid=auth_user.uid,
                    email=auth_user.email,
                    display_name=auth_user.display_name,
                    photo_url=auth_user.photo_url
                )
                user_ref = self.db.collection("users").document(user_id)
                user_ref.update(updated_user.dict())
        except UserServiceException as e:
            raise e
        except auth.UserNotFoundError:
            self.logger.debug(f"User not found in Firebase Auth: {user_id}")
            raise UserServiceException(f"User not found in Auth: {user_id}")
        except Exception as e:
            self.log_error(e, {'user_id': user_id})
            raise