from datetime import datetime
from typing import List, Optional
from google.cloud import firestore
import logging

from pydantic import ValidationError
from firebase_admin import firestore
from .base_service import BaseService
from models import Transaction
from .budget_service import BudgetService
from .category_service import CategoryService

class TransactionService(BaseService):
    """Service class for handling transaction operations."""
    
    def __init__(self, db: firestore.Client, budget_service: BudgetService = None, 
                category_service: CategoryService = None):
        """Initialize the transaction service.
        
        Args:
            db: Firestore client instance
            budget_service: Optional BudgetService instance for budget validation
            category_service: Optional CategoryService instance for category validation
        """
        super().__init__()
        self.db = db
        self.collection = "transactions"
        self.budget_service = budget_service
        self.category_service = category_service
        
    async def create_transaction(self, transaction: Transaction) -> Transaction:
        """Create a new transaction.
        
        Args:
            transaction_data: Dictionary containing transaction information
            
        Returns:
            str: ID of the created transaction
            
        Raises:
            ValueError: If required fields are missing or invalid
            FirestoreError: If there's an error with the database operation
        """
        try:
            # Validate budget and category if services are available
            if self.budget_service:
                budget = await self.budget_service.get_budget(transaction.budget_id)
                if not budget:
                    raise ValueError(f"Budget {transaction.budget_id} not found")
                    
            if self.category_service:
                category = await self.category_service.get_category(transaction.category_id)
                if not category:
                    raise ValueError(f"Category {transaction.category_id} not found")
                    
            # Add timestamps
            transaction.created_at = datetime.utcnow()
            transaction.updated_at = datetime.utcnow()
            
            # Create transaction document
            doc_ref = self.db.collection(self.collection).document()
            transaction.id = doc_ref.id
            await doc_ref.set(transaction.model_dump())
            
            return transaction
            
        except Exception as e:
            logging.error(f"Error creating transaction: {str(e)}")
            raise
            
    async def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Retrieve a transaction by ID.
        
        Args:
            transaction_id: ID of the transaction to retrieve
            
        Returns:
            Optional[Dict]: Transaction data if found, None otherwise
        """
        try:
            doc_ref = self.db.collection(self.collection).document(transaction_id)
            doc = await doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return Transaction.model_validate(data)
            return None
            
        except Exception as e:
            logging.error(f"Error retrieving transaction {transaction_id}: {str(e)}")
            raise
            
    async def update_transaction(self, transaction_id: str, 
                        transaction: Transaction) -> Optional[Transaction]:
        """Update a transaction.
        
        Args:
            transaction_id: ID of the transaction to update
            transaction_data: Dictionary containing updated transaction information
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Validate if transaction exists
            doc_ref = self.db.collection(self.collection).document(transaction_id)
            doc = await doc_ref.get()
            
            if not doc.exists:
                return None
                
            # Update timestamps
            transaction.updated_at = datetime.utcnow()
            transaction.id = transaction_id

            # Update document
            await doc_ref.update(transaction.model_dump(exclude={'id'}))
            return transaction
            
        except Exception as e:
            logging.error(f"Error updating transaction {transaction_id}: {str(e)}")
            raise
            
    async def delete_transaction(self, transaction_id: str) -> bool:
        """Delete a transaction.
        
        Args:
            transaction_id: ID of the transaction to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            doc_ref = self.db.collection(self.collection).document(transaction_id)
            doc = await doc_ref.get()
            
            if not doc.exists:
                return False
                
            await doc_ref.delete()
            return True
            
        except Exception as e:
            logging.error(f"Error deleting transaction {transaction_id}: {str(e)}")
            raise
            
    async def get_transactions_by_date_range(self, budget_id: str, 
                                    start_date: datetime,
                                    end_date: datetime) -> List[Transaction]:
        """Retrieve transactions within a date range for a specific budget.
        
        Args:
            budget_id: ID of the budget
            start_date: Start date for the range
            end_date: End date for the range
            
        Returns:
            List[Dict]: List of transactions within the date range
        """
        try:
            transactions = []
            query = (self.db.collection(self.collection)
                    .where('budget_id', '==', budget_id)
                    .where('date', '>=', start_date)
                    .where('date', '<=', end_date))
            
            docs = await query.get()
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                transactions.append(Transaction.model_validate(data))
                
            return transactions
            
        except Exception as e:
            logging.error(f"Error retrieving transactions for budget {budget_id}: {str(e)}")
            raise
            
    async def get_transactions_by_budget(self, budget_id: str) -> List[Transaction]:
        """Retrieve all transactions for a specific budget.
        
        Args:
            budget_id: ID of the budget
            
        Returns:
            List[Dict]: List of transactions for the budget
        """
        try:
            transactions = []
            query = self.db.collection(self.collection).where('budget_id', '==', budget_id)
            
            docs = await query.get()
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                transactions.append(Transaction.model_validate(data))
                
            return transactions
            
        except Exception as e:
            logging.error(f"Error retrieving transactions for budget {budget_id}: {str(e)}")
            raise

