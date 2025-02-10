from datetime import datetime
from typing import List, Dict, Any

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from models import CategoryGroup

from .base_service import BaseService
from exceptions import (
    ValidationException,
    NotFoundException,
    UnauthorizedException
)


class CategoryGroupsService(BaseService):
    """Service class for managing category groups in the application."""

    def __init__(self, db: firestore.Client):
        """Initialize the category groups service with the Firestore collection.
        
        Args:
            db: Firestore client instance
        """
        super().__init__()
        self.db = db
        self.collection = "category_groups"


    async def create_category_group(self, user_id: str, data: CategoryGroup) -> CategoryGroup:
        """
        Create a new category group.

        Args:
            user_id: ID of the user creating the category group
            data: CategoryGroup model instance

        Returns:
            CategoryGroup: The created category group

        Raises:
            ValidationException: If the input data is invalid
            UnauthorizedException: If the user is not authorized
        """
        # Ensure user_id matches
        data.user_id = user_id
        
        # Set timestamps
        now = datetime.utcnow()
        data.created_at = now
        data.updated_at = now

        # Create in database using model_dump()
        doc_ref = await self.db.collection(self.collection).add(data.model_dump(exclude={'id'}))
        data.id = doc_ref.id

        return data

    async def get_category_group(self, user_id: str, group_id: str) -> CategoryGroup:
        """
        Retrieve a category group by ID.

        Args:
            user_id: ID of the user requesting the category group
            group_id: ID of the category group to retrieve

        Returns:
            CategoryGroup: The requested category group

        Raises:
            NotFoundException: If the category group doesn't exist
            UnauthorizedException: If the user is not authorized
        """
        doc = await self.db.collection(self.collection).document(group_id).get()

        if not doc.exists:
            raise NotFoundException(f"Category group {group_id} not found")

        data = doc.to_dict()
        data['id'] = doc.id

        category_group = CategoryGroup(**data)
        if category_group.user_id != user_id:
            raise UnauthorizedException("Not authorized to access this category group")

        return category_group

    async def list_category_groups(self, user_id: str) -> List[CategoryGroup]:
        """
        List all category groups for a user.

        Args:
            user_id: ID of the user

        Returns:
            List[CategoryGroup]: List of category groups
        """
        query = self.db.collection(self.collection).where(
            filter=FieldFilter("user_id", "==", user_id)
        )
        
        docs = await query.get()
        category_groups = []
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            category_groups.append(CategoryGroup(**data))
        
        return category_groups

    async def update_category_group(
        self, user_id: str, group_id: str, data: CategoryGroup
    ) -> CategoryGroup:
        """
        Update a category group.

        Args:
            user_id: ID of the user updating the category group
            group_id: ID of the category group to update
            data: CategoryGroup model with updates

        Returns:
            CategoryGroup: The updated category group

        Raises:
            NotFoundException: If the category group doesn't exist
            ValidationException: If the input data is invalid
            UnauthorizedException: If the user is not authorized
        """
        current_group = await self.get_category_group(user_id, group_id)
        
        # Update fields from input data
        current_group.name = data.name
        current_group.categories = data.categories
        current_group.updated_at = datetime.utcnow()
        
        # Update in database
        update_data = current_group.model_dump(
            exclude={'id', 'user_id', 'created_at'}
        )
        await self.db.collection(self.collection).document(group_id).update(update_data)
        
        return current_group

    async def delete_category_group(self, user_id: str, group_id: str) -> None:
        """
        Delete a category group.

        Args:
            user_id: ID of the user deleting the category group
            group_id: ID of the category group to delete

        Raises:
            NotFoundException: If the category group doesn't exist
            UnauthorizedException: If the user is not authorized
        """
        # Verify existence and ownership
        await self.get_category_group(user_id, group_id)
        
        # Delete the document
        await self.db.collection(self.collection).document(group_id).delete()

    async def add_category_to_group(
        self, user_id: str, group_id: str, category_id: str
    ) -> Dict[str, Any]:
        """
        Add a category to a category group.

        Args:
            user_id: ID of the user
            group_id: ID of the category group
            category_id: ID of the category to add

        Returns:
            Updated category group data

        Raises:
            NotFoundException: If the category group doesn't exist
            UnauthorizedException: If the user is not authorized
        """
        category_group = await self.get_category_group(user_id, group_id)
        
        if category_id not in category_group["categories"]:
            category_group["categories"].append(category_id)
            category_group["updated_at"] = datetime.utcnow()
            
            await self.db.collection(self.collection).document(group_id).update({
                "categories": category_group["categories"],
                "updated_at": category_group["updated_at"]
            })

        return category_group

    async def remove_category_from_group(
        self, user_id: str, group_id: str, category_id: str
    ) -> Dict[str, Any]:
        """
        Remove a category from a category group.

        Args:
            user_id: ID of the user
            group_id: ID of the category group
            category_id: ID of the category to remove

        Returns:
            Updated category group data

        Raises:
            NotFoundException: If the category group doesn't exist
            UnauthorizedException: If the user is not authorized
        """
        category_group = await self.get_category_group(user_id, group_id)
        
        if category_id in category_group["categories"]:
            category_group["categories"].remove(category_id)
            category_group["updated_at"] = datetime.utcnow()
            
            await self.db.collection(self.collection).document(group_id).update({
                "categories": category_group["categories"],
                "updated_at": category_group["updated_at"]
            })

        return category_group

