from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict

class NameRequest(BaseModel):
    name: str

class User(BaseModel):
    user_id: str
    email: str
    currency: str = "USD"
    locale: str = "en_US"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    subscription_status: str = "free"
    default_budget_id: Optional[str]

class Category(BaseModel):
    category_id: str
    name: str
    assigned_amount: int  # Stored in cents

class Budget(BaseModel):
    budget_id: str
    user_id: str
    name: str
    currency: str = "USD"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    categories: List[Category] = []

class Account(BaseModel):
    account_id: str
    budget_id: str
    user_id: str
    name: str
    type: str  # checking, savings, credit card, cash
    balance: int  # Stored in cents
    currency: str = "USD"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Transaction(BaseModel):
    transaction_id: str
    account_id: str
    budget_id: str
    user_id: str
    amount: int  # Stored in cents
    currency: str = "USD"
    date: datetime
    payee: Optional[str]
    category_id: Optional[str]
    cleared: bool = False
    notes: Optional[str]

class RecurringTransaction(BaseModel):
    recurring_id: str
    budget_id: str
    user_id: str
    amount: int  # Stored in cents
    currency: str = "USD"
    category_id: Optional[str]
    next_due_date: datetime
    frequency: str  # daily, weekly, biweekly, monthly, yearly

class Currency(BaseModel):
    currency_code: str
    exchange_rates: Dict[str, float]
    last_updated: datetime = Field(default_factory=datetime.utcnow)