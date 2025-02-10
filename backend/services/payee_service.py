from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from firebase_admin import firestore
import logging
from .base_service import BaseService
from models import Payee
from exceptions import ValidationException, NotFoundException


class MerchantType(str, Enum):
    RETAIL = "retail"
    RESTAURANT = "restaurant"
    SERVICES = "services"
    UTILITY = "utility"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class PayeeSearchResult(BaseModel):
    payees: List[Payee]
    total_count: int
    query: str


class PayeeService(BaseService):
    def __init__(self, db: firestore.Client):
        super().__init__()
        self.db = db
        self.collection = 'payees'
        self.logger = logging.getLogger(__name__)

    def create_payee(self, payee: Payee) -> Payee:
        """Create a new payee.
        
        Args:
            payee: Pydantic Payee model instance with payee data
            
        Returns:
            Payee: Created payee with ID
            
        Raises:
            ValidationException: If category validation fails or merchant type is invalid
        """
        try:
            if payee.merchant_type and payee.merchant_type not in MerchantType:
                raise ValidationException(f"Invalid merchant type: {payee.merchant_type}")
                
            if payee.default_category_id:
                self._validate_category_exists(payee.default_category_id)
                
            payee.created_at = datetime.utcnow()
            payee.updated_at = datetime.utcnow()
            payee.last_used = None
            doc_ref = self.db.collection(self.collection).document()
            doc_ref.set(payee.model_dump())
            payee.id = doc_ref.id
            return payee
        except Exception as e:
            self.logger.error(f"Error creating payee: {str(e)}")
            raise

    def get_payee(self, payee_id: str) -> Optional[Payee]:
        """Get a payee by ID."""
        try:
            doc = self.db.collection(self.collection).document(payee_id).get()
            if not doc.exists:
                return None
            payee_data = doc.to_dict()
            payee_data['id'] = doc.id
            return Payee(**payee_data)
        except Exception as e:
            self.logger.error(f"Error getting payee {payee_id}: {str(e)}")
            raise

    def update_payee(self, payee_id: str, payee: Payee) -> Payee:
        """Update a payee.
        
        Args:
            payee_id: ID of payee to update
            payee: Pydantic Payee model with updated data
            
        Returns:
            Payee: Updated payee
            
        Raises:
            NotFoundException: If payee not found
            ValidationException: If category validation fails
        """
        try:
            doc_ref = self.db.collection(self.collection).document(payee_id)
            doc = doc_ref.get()
            if not doc.exists:
                raise NotFoundException(f"Payee {payee_id} not found")
            
            if payee.default_category_id:
                self._validate_category_exists(payee.default_category_id)
                
            payee.updated_at = datetime.utcnow()
            doc_ref.update(payee.model_dump(exclude_unset=True))
            
            updated_doc = doc_ref.get()
            payee_data = updated_doc.to_dict()
            payee_data['id'] = doc.id
            return Payee(**payee_data)
        except Exception as e:
            self.logger.error(f"Error updating payee {payee_id}: {str(e)}")
            raise

    def delete_payee(self, payee_id: str) -> None:
        """Delete a payee."""
        try:
            doc_ref = self.db.collection(self.collection).document(payee_id)
            if not doc_ref.get().exists:
                raise NotFoundException(f"Payee {payee_id} not found")
            doc_ref.delete()
        except Exception as e:
            self.logger.error(f"Error deleting payee {payee_id}: {str(e)}")
            raise

    def add_alias(self, payee_id: str, alias: str) -> Payee:
        """Add an alias to a payee."""
        try:
            doc_ref = self.db.collection(self.collection).document(payee_id)
            doc = doc_ref.get()
            if not doc.exists:
                raise NotFoundException(f"Payee {payee_id} not found")
            
            payee_data = doc.to_dict()
            aliases = payee_data.get('aliases', [])
            if alias not in aliases:
                aliases.append(alias)
                doc_ref.update({
                    'aliases': aliases,
                    'updated_at': datetime.utcnow()
                })
            
            updated_doc = doc_ref.get()
            payee_data = updated_doc.to_dict()
            payee_data['id'] = doc.id
            return Payee(**payee_data)
        except Exception as e:
            self.logger.error(f"Error adding alias to payee {payee_id}: {str(e)}")
            raise

    def update_last_used(self, payee_id: str) -> None:
        """Update the last used date of a payee."""
        try:
            doc_ref = self.db.collection(self.collection).document(payee_id)
            doc_ref.update({
                'last_used': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
        except Exception as e:
            self.logger.error(f"Error updating last used date for payee {payee_id}: {str(e)}")
            raise

    def search_payees(self, query: str, user_id: str) -> PayeeSearchResult:
        """Search payees by name or alias.
        
        Args:
            query: Search string to match against name or aliases
            user_id: ID of the user to search payees for
            
        Returns:
            PayeeSearchResult containing matching payees and metadata
            
        Raises:
            Exception: If there is an error performing the search
        """
        try:
            payees = []
            # Search by name
            name_docs = self.db.collection(self.collection)\
                .where('user_id', '==', user_id)\
                .where('name', '>=', query)\
                .where('name', '<=', query + '\uf8ff')\
                .stream()
            
            for doc in name_docs:
                payee_data = doc.to_dict()
                payee_data['id'] = doc.id
                payees.append(Payee.model_validate(payee_data))
            
            # Search by alias
            alias_docs = self.db.collection(self.collection)\
                .where('user_id', '==', user_id)\
                .where('aliases', 'array_contains', query)\
                .stream()
            
            for doc in alias_docs:
                if doc.id not in [p.id for p in payees]:
                    payee_data = doc.to_dict()
                    payee_data['id'] = doc.id
                    payees.append(Payee.model_validate(payee_data))
            
            return PayeeSearchResult(
                payees=payees,
                total_count=len(payees),
                query=query
            )
        except Exception as e:
            self.logger.error(f"Error searching payees: {str(e)}")
            raise

    def get_payees_by_merchant_type(self, merchant_type: MerchantType, user_id: str) -> List[Payee]:
        """Get all payees of a specific merchant type.
        
        Args:
            merchant_type: Type of merchant to filter by, must be a valid MerchantType
            user_id: ID of the user to get payees for
            
        Returns:
            List of payees matching the merchant type
            
        Raises:
            ValidationException: If merchant type is invalid
        """
        try:
            if merchant_type not in MerchantType:
                raise ValidationException(f"Invalid merchant type: {merchant_type}")
                
            payees = []
            docs = self.db.collection(self.collection)\
                .where('user_id', '==', user_id)\
                .where('merchant_type', '==', merchant_type)\
                .stream()
            
            for doc in docs:
                payee_data = doc.to_dict()
                payee_data['id'] = doc.id
                payees.append(Payee(**payee_data))
            return payees
        except Exception as e:
            self.logger.error(f"Error getting payees by merchant type: {str(e)}")
            raise


    def _validate_category_exists(self, category_id: str) -> None:
        """Validate that a category exists."""
        category_ref = self.db.collection('categories').document(category_id)
        if not category_ref.get().exists:
            raise ValidationException(f"Category {category_id} does not exist")

