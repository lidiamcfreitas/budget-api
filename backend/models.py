from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from enum import Enum
from firebase_admin import firestore
# Store valid currencies in a separate JSON file
import json

CURRENCY_FILE = "data/valid_currencies.json"

# Load valid currencies from JSON file
with open(CURRENCY_FILE, "r") as file:
    VALID_CURRENCIES = set(json.load(file))

class FrequencyType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class BaseAuditModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def update(self, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().copy(update=kwargs)

    @classmethod
    def generate_id(cls, db: firestore.Client, collection_path: str) -> str:
        """Generate a new Firestore document ID."""
        return db.collection(collection_path).document().id

    @classmethod
    def create(cls, db: firestore.Client, collection_path: str, **data):
        """Create a new document with a generated ID."""
        doc_id = cls.generate_id(db, collection_path)
        instance = cls(id=doc_id, **data)
        db.collection(collection_path).document(doc_id).set(instance.dict())
        return instance

class User(BaseAuditModel):
    email: str
    name: Optional[str] = None
    default_budget_id: Optional[str] = None

class Budget(BaseAuditModel):
    user_id: str
    name: str
    currency: str

    def document_path(self) -> str:
        return f"users/{self.user_id}/budgets/{self.budget_id}"

class Payee(BaseAuditModel):
    user_id: str
    name: str
    default_category_id: Optional[str]  # Default category for this payee
    merchant_type: Optional[str]  # Classification like groceries, utilities, etc.
    last_used: Optional[datetime]  # Last transaction date with this payee
    imported_aliases: Optional[List[str]]  # Imported payees that match these will be renamed.

class CategoryGroup(BaseAuditModel):
    user_id: str
    budget_id: str
    name: str

class Category(BaseAuditModel):
    group_id: str
    name: str
    cash_left_over: int = 0 # Cash left over from last month
    target_id : Optional[str] = None # Target savings for this category
    assigned_amounts: Dict[str, int] = {}  # Stores assigned amounts by month
    notes: Optional[str] = "" # User notes
    # Target
    target_amount: Optional[int] = None
    target_type: Optional[str] = None  # "weekly", "monthly", "yearly", "by date", "custom"
    target_due_date: Optional[datetime] = None

    def get_transactions(self, month: Optional[str] = None) -> List[Dict]:
        """Fetch all transactions for this category and optionally filter by month."""
        db = firestore.Client()
        query = db.collection("transactions")\
            .where("category_id", "==", self.id)\
            .where("user_id", "==", self.user_id)\
            .where("budget_id", "==", self.budget_id)
        
        if month:
            start_date = datetime.strptime(month, "%Y-%m").replace(day=1)
            next_month = (start_date + timedelta(days=32)).replace(day=1)
            query = query.where("date", ">=", start_date).where("date", "<", next_month)
        
        return [txn.to_dict() for txn in query.get()]  # Uses Firestore caching

    def get_cash_spending(self, month: Optional[str] = None) -> int:
        return sum(txn["amount"] for txn in self.get_transactions(month) if txn["account_type"] == "cash")

    def get_credit_spending(self, month: Optional[str] = None) -> int:
        return sum(txn["amount"] for txn in self.get_transactions(month) if txn["account_type"] == "credit")

    def get_assigned_amount(self, month: str) -> int:
        return self.assigned_amounts.get(month, 0)
    
    def set_assigned_amount(self, month: str, amount: int):
        self.assigned_amounts[month] = amount

    @property
    def assigned_this_month(self) -> int:
        current_month = datetime.utcnow().strftime("%Y-%m")
        return self.get_assigned_amount(current_month)

    @property
    def assigned_last_month(self) -> int:
        last_month = (datetime.utcnow().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        return self.get_assigned_amount(last_month)

    @property
    def available_balance(self) -> int:
        return self.cash_left_over + self.assigned_this_month - (self.get_cash_spending() + self.get_credit_spending())

    @property
    def spent_last_month(self) -> int:
        last_month = (datetime.utcnow().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        return self.get_cash_spending(last_month) + self.get_credit_spending(last_month)

    @property
    def to_go(self) -> int:
        if not self.target:
            return 0
        return max(0, self.target_amount - self.assigned_this_month)


class Account(BaseAuditModel):
    budget_id: str
    user_id: str
    name: str
    account_type: str  # checking, savings, credit card, cash
    balance: int  # Stored in cents
    currency: str

    @property
    def document_path(self) -> str:
        return f"users/{self.user_id}/budgets/{self.budget_id}/accounts/{self.id}"

class Transaction(BaseAuditModel):
    account_id: str
    amount: int  # Stored in cents
    date: datetime
    payee: Optional[str]
    category_id: Optional[str]
    cleared: bool = False
    notes: Optional[str]
    pending: bool = False

    @property
    def document_path(self) -> str:
        return f"users/{self.user_id}/budgets/{self.budget_id}/accounts/{self.account_id}/transactions/{self.id}"

class RecurringTransaction(Transaction):
    next_due_date: datetime
    frequency: FrequencyType  # Type of recurrence (daily, weekly, monthly, yearly)

class CrossBudgetTransfer(BaseAuditModel):
    from_budget_id: str
    to_budget_id: str
    from_account_id: str
    to_account_id: str
    from_amount: int  # Stored in cents. Amounts will differ if currencies are different.
    to_amount: int  # Stored in cents. Amounts will differ if currencies are different.
    date: datetime
    notes: Optional[str]

class Currency(BaseModel):
    currency_code: str
    exchange_rates: Dict[str, float]
    last_updated: datetime = Field(default_factory=datetime.utcnow)
