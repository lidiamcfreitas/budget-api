from google.cloud import firestore
from models import User, Budget, Account, Transaction, RecurringTransaction, Currency

# Initialize Firestore client
db = firestore.Client()

# User operations
def create_user(user: User):
    if get_user(user.user_id):
        raise ValueError("User already exists.")
    user_ref = db.collection("users").document(user.user_id)
    user_ref.set(user.dict())

def get_user(user_id: str):
    user_ref = db.collection("users").document(user_id).get()
    return user_ref.to_dict() if user_ref.exists else None

# Budget operations
def create_budget(budget: Budget):
    if not get_user(budget.user_id):
        raise ValueError("User does not exist.")
    budget_ref = db.collection("budgets").document(budget.budget_id)
    budget_ref.set(budget.dict())

def get_budget(budget_id: str):
    budget_ref = db.collection("budgets").document(budget_id).get()
    return budget_ref.to_dict() if budget_ref.exists else None

# Account operations
def create_account(account: Account):
    if not get_user(account.user_id):
        raise ValueError("User does not exist.")
    if not get_budget(account.budget_id):
        raise ValueError("Budget does not exist.")
    account_ref = db.collection("accounts").document(account.account_id)
    account_ref.set(account.dict())

def get_account(account_id: str):
    account_ref = db.collection("accounts").document(account_id).get()
    return account_ref.to_dict() if account_ref.exists else None

# Transaction operations
def create_transaction(transaction: Transaction):
    if not get_account(transaction.account_id):
        raise ValueError("Account does not exist.")
    budget = get_budget(transaction.budget_id)
    if not budget:
        raise ValueError("Budget does not exist.")
    
    # Validate category exists in budget
    if transaction.category_id:
        category_ids = [category["category_id"] for category in budget.get("categories", [])]
        if transaction.category_id not in category_ids:
            raise ValueError("Category does not exist in the budget.")
    
    transaction_ref = db.collection("transactions").document(transaction.transaction_id)
    transaction_ref.set(transaction.dict())

def get_transaction(transaction_id: str):
    transaction_ref = db.collection("transactions").document(transaction_id).get()
    return transaction_ref.to_dict() if transaction_ref.exists else None

# Recurring Transaction operations
def create_recurring_transaction(recurring_transaction: RecurringTransaction):
    if not get_budget(recurring_transaction.budget_id):
        raise ValueError("Budget does not exist.")
    
    recurring_ref = db.collection("recurringTransactions").document(recurring_transaction.recurring_id)
    recurring_ref.set(recurring_transaction.dict())

def get_recurring_transaction(recurring_id: str):
    recurring_ref = db.collection("recurringTransactions").document(recurring_id).get()
    return recurring_ref.to_dict() if recurring_ref.exists else None

# Currency operations
def update_currency_rates(currency: Currency):
    currency_ref = db.collection("currencies").document(currency.currency_code)
    currency_ref.set(currency.dict())

def get_currency_rate(currency_code: str):
    currency_ref = db.collection("currencies").document(currency_code).get()
    return currency_ref.to_dict() if currency_ref.exists else None