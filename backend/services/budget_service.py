from typing import List, Optional
from datetime import datetime
from firebase_admin import firestore
from .base_service import BaseService
from models import Budget

class BudgetService(BaseService):
    """Service for managing budget operations."""
    
    def __init__(self, db: firestore.Client):
        """Initialize BudgetService with database client.
        """
        super().__init__()
        self.db = db
        self.collection = 'budgets'
    
    async def create_budget(self, budget: Budget) -> Budget:
        """Create a new budget for a user.
        
        Args:
            budget: Budget model instance containing budget details
                
        Returns:
            Budget: Newly created budget object
            
        Raises:
            ValueError: If validation fails
            FirebaseError: If database operation fails
        """
        try:
            user_id = budget.user_id
            self.logger.info(f"Creating new budget for user {user_id}")
            
            doc_ref = self.db.collection(self.collection).document()
            budget.budget_id = doc_ref.id
            doc_ref.set(budget.dict())
            
            return budget
            
        except Exception as e:
            self.logger.error(f"Error creating budget: {str(e)}")
            raise
    
    async def get_budget(self, budget_id: str) -> Optional[Budget]:
        """Retrieve a specific budget by ID.
        
        Args:
            budget_id: ID of the budget to retrieve
            
        Returns:
            Budget: Budget object if found, None otherwise
            
        Raises:
            FirebaseError: If database operation fails
        """
        try:
            self.logger.info(f"Retrieving budget {budget_id}")
            doc_ref = self.db.collection(self.collection).document(budget_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['budget_id'] = doc.id
                return Budget(**data)
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving budget: {str(e)}")
            raise
    
    async def get_user_budgets(self, user_id: str) -> List[Budget]:
        """Retrieve all budgets for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List[Budget]: List of budget objects
            
        Raises:
            FirebaseError: If database operation fails
        """
        try:
            self.logger.info(f"Retrieving budgets for user {user_id}")
            docs = self.db.collection(self.collection)\
                .where('user_id', '==', user_id)\
                .stream()
            
            budgets = []
            for doc in docs:
                data = doc.to_dict()
                data['budget_id'] = doc.id
                budgets.append(Budget(**data))
            
            return budgets
            
        except Exception as e:
            self.logger.error(f"Error retrieving user budgets: {str(e)}")
            raise
    
    async def update_budget(self, budget_id: str, budget: Budget) -> Budget:
        """Update an existing budget.
        
        Args:
            budget_id: ID of the budget to update
            budget: Budget model instance containing fields to update
            
        Returns:
            Budget: Updated budget object
            
        Raises:
            ValueError: If budget not found
            FirebaseError: If database operation fails
        """
        try:
            self.logger.info(f"Updating budget {budget_id}")
            doc_ref = self.db.collection(self.collection).document(budget_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                raise ValueError(f"Budget {budget_id} not found")
            
            # Get existing data and update with new budget data
            existing_budget = Budget(**doc.to_dict())
            new_budget = existing_budget.update(**budget.dict())
            
            doc_ref.update(new_budget.dict())
            
            # Get updated document
            updated_doc = doc_ref.get()
            updated_data = updated_doc.to_dict()
            updated_data['budget_id'] = updated_doc.id
            
            return Budget(**updated_data)
            
        except Exception as e:
            self.logger.error(f"Error updating budget: {str(e)}")
            raise
    
    async def delete_budget(self, budget_id: str) -> bool:
        """Delete a budget.
        
        Args:
            budget_id: ID of the budget to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            ValueError: If budget not found
            FirebaseError: If database operation fails
        """
        try:
            self.logger.info(f"Deleting budget {budget_id}")
            doc_ref = self.db.collection(self.collection).document(budget_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                raise ValueError(f"Budget {budget_id} not found")
            
            doc_ref.delete()
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting budget: {str(e)}")
            raise
