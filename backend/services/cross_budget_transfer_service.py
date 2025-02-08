from datetime import datetime
from typing import List, Optional
from google.cloud import firestore
from models import CrossBudgetTransfer
from .base_service import BaseService
from .account_service import AccountService

class CrossBudgetTransferService(BaseService):
    def __init__(self, db: firestore.Client, account_service: AccountService):
        super().__init__()
        self.db = db
        self.account_service = account_service
        self.collection = 'cross_budget_transfers'

    def create_transfer(self, transfer: CrossBudgetTransfer) -> CrossBudgetTransfer:
        """Create a new cross-budget transfer.
        
        Args:
            transfer: CrossBudgetTransfer model containing transfer details
            
        Returns:
            CrossBudgetTransfer: Created transfer with updated status and ID
            
        Raises:
            ValueError: If source or destination account validation fails
        """
        try:
            # Validate accounts and currencies
            source_account = self.account_service.get_account(transfer.source_account_id)
            dest_account = self.account_service.get_account(transfer.destination_account_id)
            
            if not source_account or not dest_account:
                raise ValueError("Source or destination account not found")

            if source_account.budget_id == dest_account.budget_id:
                raise ValueError("Accounts must belong to different budgets")

            # Handle currency conversion if needed
            amount_dest = self._convert_currency(
                transfer.amount,
                source_account.currency,
                dest_account.currency
            )

            # Update transfer model
            transfer.created_at = datetime.utcnow()
            transfer.updated_at = datetime.utcnow()
            transfer.status = 'pending'
            transfer.amount_destination = amount_dest

            # Execute transfer atomically
            completed_transfer = self._execute_transfer(transfer)

            self.logger.info(f"Created cross-budget transfer {completed_transfer.id}")
            return completed_transfer
        except Exception as e:
            self.logger.error(f"Error creating cross-budget transfer: {str(e)}")
            raise

    def _execute_transfer(self, transfer: CrossBudgetTransfer) -> CrossBudgetTransfer:
        """Execute the transfer atomically.
        
        Args:
            transfer: CrossBudgetTransfer model containing transfer details
            
        Returns:
            CrossBudgetTransfer: Completed transfer with updated status
            
        Raises:
            ValueError: If transfer execution fails
        """
        transaction = self.db.transaction()
        
        @firestore.transactional
        def transfer_in_transaction(transaction):
            # Create transfer record
            transfer_ref = self.db.collection(self.collection).document()
            
            # Update source account
            self.account_service.update_balance(
                transfer.source_account_id,
                -transfer.amount
            )
            
            # Update destination account
            self.account_service.update_balance(
                transfer.destination_account_id,
                transfer.amount_destination
            )
            
            # Save transfer record
            transfer.status = 'completed'
            transfer.id = transfer_ref.id
            transfer_ref.set(transfer.model_dump())
            
            return transfer
        
        return transfer_in_transaction(transaction)

    def get_transfer(self, transfer_id: str) -> Optional[CrossBudgetTransfer]:
        """Get transfer by ID.
        
        Args:
            transfer_id: ID of the transfer to retrieve
            
        Returns:
            Optional[CrossBudgetTransfer]: Transfer if found, None otherwise
            
        Raises:
            Exception: If database operation fails
        """
        try:
            doc = self.db.collection(self.collection).document(transfer_id).get()
            return CrossBudgetTransfer(**doc.to_dict()) if doc.exists else None
        except Exception as e:
            self.logger.error(f"Error getting transfer {transfer_id}: {str(e)}")
            raise

    def get_transfers_by_budget(self, budget_id: str) -> List[CrossBudgetTransfer]:
        """Get all transfers for a budget (both source and destination).
        
        Args:
            budget_id: ID of the budget to get transfers for
            
        Returns:
            List[CrossBudgetTransfer]: List of transfers related to the budget
            
        Raises:
            Exception: If database operation fails
        """
        try:
            source_transfers = self.db.collection(self.collection).where('source_budget_id', '==', budget_id).stream()
            dest_transfers = self.db.collection(self.collection).where('destination_budget_id', '==', budget_id).stream()
            
            return [CrossBudgetTransfer(**doc.to_dict()) for doc in source_transfers] + \
                [CrossBudgetTransfer(**doc.to_dict()) for doc in dest_transfers]
        except Exception as e:
            self.logger.error(f"Error getting transfers for budget {budget_id}: {str(e)}")
            raise

    def _convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount between currencies.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Destination currency code
            
        Returns:
            float: Converted amount
        """
        if from_currency == to_currency:
            return amount
            
        # TODO: Implement actual currency conversion using exchange rates
        # For now, return the same amount
        return amount
