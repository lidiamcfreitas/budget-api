from datetime import datetime
from typing import List, Optional
from pydantic import ValidationError
from models import Account
from google.cloud import firestore
from models import Account
from .base_service import BaseService

class AccountService(BaseService):
    def __init__(self, db: firestore.Client):
        super().__init__()
        self.db = db
        self.collection = 'accounts'

    def create_account(self, account: Account) -> str:
        """Create a new account.
        
        Args:
            account: Account model instance with account details
        
        Returns:
            str: The ID of the created account
        
        Raises:
            ValidationError: If account data is invalid
            Exception: If there's an error creating the account
        """
        try:
            account.created_at = datetime.utcnow()
            account.updated_at = datetime.utcnow()
            
            doc_ref = self.db.collection(self.collection).document()
            doc_ref.set(account.model_dump(exclude_none=True))
            
            self.logger.info(f"Created account {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            self.logger.error(f"Error creating account: {str(e)}")
            raise

    def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID.
        
        Args:
            account_id: The ID of the account to retrieve
        
        Returns:
            Optional[Account]: The account if found, None otherwise
        
        Raises:
            Exception: If there's an error retrieving the account
        """
        try:
            doc = self.db.collection(self.collection).document(account_id).get()
            if doc.exists:
                account_data = doc.to_dict()
                account_data['id'] = doc.id
                return Account(**account_data)
            return None
        except Exception as e:
            self.logger.error(f"Error getting account {account_id}: {str(e)}")
            raise

    def update_account(self, account_id: str, account: Account) -> bool:
        """Update an existing account.
        
        Args:
            account_id: The ID of the account to update
            account: Account model instance with updated details
        
        Returns:
            bool: True if update successful
        
        Raises:
            ValidationError: If account data is invalid
            Exception: If there's an error updating the account
        """
        try:
            account.updated_at = datetime.utcnow()
            
            doc_ref = self.db.collection(self.collection).document(account_id)
            doc_ref.update(account.model_dump(exclude_unset=True, exclude_none=True))
            
            self.logger.info(f"Updated account {account_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating account {account_id}: {str(e)}")
            raise

    def delete_account(self, account_id: str) -> bool:
        """Delete an account."""
        try:
            self.db.collection(self.collection).document(account_id).delete()
            self.logger.info(f"Deleted account {account_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting account {account_id}: {str(e)}")
            raise

    def update_balance(self, account_id: str, amount: float) -> bool:
        """Update account balance atomically."""
        try:
            transaction = self.db.transaction()
            
            @firestore.transactional
            def update_in_transaction(transaction, doc_ref, amount):
                doc = doc_ref.get(transaction=transaction)
                if not doc.exists:
                    raise ValueError("Account not found")
                
                current_balance = doc.get('balance', 0)
                new_balance = current_balance + amount
                
                transaction.update(doc_ref, {
                    'balance': new_balance,
                    'updated_at': datetime.utcnow()
                })
            
            doc_ref = self.db.collection(self.collection).document(account_id)
            update_in_transaction(transaction, doc_ref, amount)
            
            self.logger.info(f"Updated balance for account {account_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating balance for account {account_id}: {str(e)}")
            raise

    def get_accounts_by_budget(self, budget_id: str) -> List[Account]:
        """Get all accounts for a specific budget.
        
        Args:
            budget_id: The ID of the budget to get accounts for
        
        Returns:
            List[Account]: List of accounts belonging to the budget
        
        Raises:
            Exception: If there's an error retrieving the accounts
        """
        try:
            docs = self.db.collection(self.collection).where('budget_id', '==', budget_id).stream()
            return [Account(**{**doc.to_dict(), 'id': doc.id}) for doc in docs]
        except Exception as e:
            self.logger.error(f"Error getting accounts for budget {budget_id}: {str(e)}")
            raise

