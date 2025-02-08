from datetime import datetime, timedelta
from typing import Optional
from google.cloud import firestore
from models import RecurringTransaction, FrequencyType, Transaction
from .transaction_service import TransactionService
from firebase_admin import firestore


class RecurringTransactionService(TransactionService):
    def __init__(self, db: firestore.Client):
        super().__init__()
        self.db = db
        self.collection = 'recurring_transactions'

    def create_recurring_transaction(self, transaction: RecurringTransaction) -> str:
        """Create a new recurring transaction.
        
        Args:
            transaction: RecurringTransaction model containing the transaction details
        
        Returns:
            str: The ID of the created recurring transaction
        
        Raises:
            ValueError: If the transaction data is invalid
        """
        """Create a new recurring transaction."""
        try:
            # Set timestamps
            transaction.created_at = datetime.utcnow()
            transaction.updated_at = datetime.utcnow()
            transaction.next_date = self.calculate_next_date(
                transaction.start_date,
                transaction.frequency_type,
                transaction.frequency_interval
            )
            
            doc_ref = self.db.collection(self.collection).document()
            doc_ref.set(transaction.model_dump())
            
            self.logger.info(f"Created recurring transaction {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            self.logger.error(f"Error creating recurring transaction: {str(e)}")
            raise

    def generate_transaction(self, recurring_id: str) -> Optional[str]:
        """Generate a regular transaction from a recurring one.
        
        Args:
            recurring_id: ID of the recurring transaction
        
        Returns:
            Optional[str]: The ID of the generated transaction if one was created, None otherwise
            
        Raises:
            ValueError: If the recurring transaction is not found or data is invalid
        """
        """Generate a regular transaction from a recurring one."""
        try:
            recurring = self.get_recurring_transaction(recurring_id)
            if not recurring:
                raise ValueError("Recurring transaction not found")
            
            if recurring['next_date'] > datetime.now():
                return None
            
            # Create regular transaction from recurring data
            transaction = Transaction(
                amount=recurring.amount,
                description=recurring.description,
                account_id=recurring.account_id,
                budget_id=recurring.budget_id,
                category_id=recurring.category_id,
                date=recurring.next_date,
                recurring_id=recurring_id
            )
            
            # Create the transaction
            transaction_id = self.create_transaction(transaction)
            
            # Update next date
            next_date = self.calculate_next_date(
                recurring['next_date'],
                recurring['frequency_type'],
                recurring['frequency_interval']
            )
            
            self.update_recurring_transaction(recurring_id, {'next_date': next_date})
            
            return transaction_id
        except Exception as e:
            self.logger.error(f"Error generating transaction for recurring {recurring_id}: {str(e)}")
            raise

    def calculate_next_date(self, base_date: datetime, frequency_type: str, interval: int) -> datetime:
        """Calculate the next occurrence date."""
        if frequency_type == FrequencyType.DAILY.value:
            return base_date + timedelta(days=interval)
        elif frequency_type == FrequencyType.WEEKLY.value:
            return base_date + timedelta(weeks=interval)
        elif frequency_type == FrequencyType.MONTHLY.value:
            return base_date.replace(month=((base_date.month - 1 + interval) % 12) + 1)
        elif frequency_type == FrequencyType.YEARLY.value:
            return base_date.replace(year=base_date.year + interval)
        else:
            raise ValueError(f"Invalid frequency type: {frequency_type}")

    def get_due_transactions(self) -> list[RecurringTransaction]:
        """Get all recurring transactions due for processing.
        
        Returns:
            list[RecurringTransaction]: List of recurring transactions that are due
            
        Raises:
            Exception: If there's an error accessing the database
        """
        try:
            now = datetime.utcnow()
            docs = (self.db.collection(self.collection)
                .where('next_date', '<=', now)
                .where('active', '==', True)
                .stream())
            return [RecurringTransaction.model_validate(doc.to_dict()) for doc in docs]
        except Exception as e:
            self.logger.error(f"Error getting due transactions: {str(e)}")
            raise

