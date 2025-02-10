from datetime import datetime
from typing import List, Optional
from firebase_admin import firestore
from .base_service import BaseService, ServiceException
from models import Category

class CategoryServiceException(ServiceException):
    """Specific exception class for category-related errors."""
    pass

class CategoryNotFoundError(CategoryServiceException):
    """Exception raised when a category is not found."""
    pass

class CategoryService(BaseService):
    """Service class for managing budget categories."""
    
    def __init__(self, db: firestore.Client):
        """Initialize the category service with database client.
        """
        super().__init__()
        self.db = db
        self.collection = "categories"
        
    async def create_category(self, user_id: str, category: Category) -> Category:
        """Create a new budget category.
        
        Args:
            user_id: ID of the user creating the category
            category: Category model instance
            
        Returns:
            Category: Newly created category object
        """
        category_dict = category.model_dump(exclude={'id'})
        category_dict.update({
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        doc_ref = self.db.collection(self.collection).document()
        await doc_ref.set(category)
        
        category["id"] = doc_ref.id
        return Category(**category)
        
    async def get_category(self, category_id: str, user_id: str) -> Category:
        """Retrieve a specific category by ID.
        
        Args:
            category_id: ID of the category to retrieve
            user_id: ID of the user requesting the category
            
        Returns:
            Category: Retrieved category object
            
        Raises:
            CategoryNotFoundError: If category doesn't exist or belongs to another user
        """
        doc_ref = self.db.collection(self.collection).document(category_id)
        category = await doc_ref.get()
        
        if not category.exists or category.get("user_id") != user_id:
            raise CategoryNotFoundError(f"Category {category_id} not found")
            
        category_data = category.to_dict()
        category_data["id"] = category_id
        return Category(**category_data)
        
    async def get_user_categories(self, user_id: str) -> List[Category]:
        """Retrieve all categories for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List[Category]: List of user's categories
        """
        categories = []
        query = self.db.collection(self.collection).where("user_id", "==", user_id)
        
        async for doc in query.stream():
            category_data = doc.to_dict()
            category_data["id"] = doc.id
            categories.append(Category(**category_data))
            
        return categories
        
    async def update_category(self, category_id: str, user_id: str, 
                            category: Category) -> Category:
        """Update an existing category.
        
        Args:
            category_id: ID of the category to update
            user_id: ID of the user making the update
            category: Category model with updated fields
            
        Returns:
            Category: Updated category object
            
        Raises:
            CategoryNotFoundError: If category doesn't exist or belongs to another user
        """
        await self.get_category(category_id, user_id)
        
        update_dict = category.model_dump(exclude_unset=True, exclude={'id', 'user_id'})
        update_dict["updated_at"] = datetime.utcnow()
            
        doc_ref = self.db.collection(self.collection).document(category_id)
        await doc_ref.update(update_dict)
        
        return await self.get_category(category_id, user_id)
        
    async def delete_category(self, category_id: str, user_id: str) -> None:
        """Delete a category.
        
        Args:
            category_id: ID of the category to delete
            user_id: ID of the user making the deletion
            
        Raises:
            CategoryNotFoundError: If category doesn't exist or belongs to another user
        """
        # Verify category exists and belongs to user
        await self.get_category(category_id, user_id)
        
        doc_ref = self.db.collection(self.collection).document(category_id)
        await doc_ref.delete()
        
