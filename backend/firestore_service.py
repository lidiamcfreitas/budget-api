import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Optional, Dict, Any
from models import User, Budget, Account, Transaction, RecurringTransaction, Currency
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more details
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)  # Use a named logger

# Path to your Firebase service account key JSON file
FIREBASE_CREDENTIALS_PATH = "/Users/lidiafreitas/programming/keys/budgetapp-449511-firebase-adminsdk-fbsvc-80fc508f2e.json"

# Check if Firebase has already been initialized
# if not firebase_admin._apps:
#     cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
#     firebase_admin.initialize_app(cred)

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {
        "projectId": "budgetapp-449511",
        # "databaseURL": f"https://firestore.googleapis.com/v1/projects/budgetapp-449511/databases/(default)/documents",
        # "databaseURL": "https://firestore.googleapis.com/v1/projects/budgetapp-449511/databases/budget-api-firestore/documents",
    })

# Use the correct Firestore database
db = firestore.client()

# User operations
def create_user(user: User) -> None:
    if get_user(user.user_id):
        raise ValueError("User already exists.")
    user_ref = db.collection("users").document(user.user_id)
    user_ref.set(user.dict())

def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    logger.info(f"Getting user with ID: {user_id}")
    try:
        user_ref = db.collection("users").document(user_id).get()
        logger.info(f"User data: {user_ref.to_dict()}")
    except Exception as e:
        logger.error(f"Error getting user: {e}")

    return user_ref.to_dict() if user_ref.exists else None

# Budget operations
def find_existing_budget(user_id: str, name: str, currency: str) -> Optional[Budget]:
    """
    Check if a budget with the same name and currency exists for the user.
    
    Args:
        user_id (str): The user ID to check for
        name (str): The budget name to check
        currency (str): The currency to check
        
    Returns:
        Optional[Budget]: The existing budget if found, None otherwise
    """
    try:
        # Query budgets collection with filters
        budgets_ref = (
            db.collection("budgets")
            .where("user_id", "==", user_id)
            .where("name", "==", name)
            .where("currency", "==", currency)
            .limit(1)
            .stream()
        )
        
        # Check if any matching budget exists
        for doc in budgets_ref:
            budget_data = doc.to_dict()
            try:
                return Budget(**budget_data)
            except ValidationError as ve:
                logger.error(f"Error converting budget {doc.id} to model: {ve}")
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"Error finding existing budget: {e}")
        return None

def create_budget(budget: Budget) -> Budget:
    try:
        # Check if user exists
        if not get_user(budget.user_id):
            raise ValueError("User does not exist.")
        
        # Check for existing budget with same name and currency
        existing_budget = find_existing_budget(budget.user_id, budget.name, budget.currency)
        if existing_budget:
            logger.info(f"Found existing budget with ID: {existing_budget.budget_id}")
            return existing_budget
        
        # Generate new document reference with auto ID
        budget_ref = db.collection("budgets").document()
        # Assign the generated ID to the model
        budget.budget_id = budget_ref.id
        # Save the data
        budget_ref.set(budget.dict())
        logger.info(f"Created budget with ID: {budget.budget_id}")
        return budget
    except Exception as e:
        logger.error(f"Error creating budget: {e}")
        raise

def get_budget(budget_id: str) -> Optional[Dict[str, Any]]:
    budget_ref = db.collection("budgets").document(budget_id).get()
    return budget_ref.to_dict() if budget_ref.exists else None

def get_user_budgets(user_id: str) -> List[Budget]:
    """
    Retrieve all budgets for a specific user from Firestore.
    
    Args:
        user_id (str): The ID of the user whose budgets to retrieve
    
    Returns:
        List[Budget]: List of Budget objects belonging to the user
    
    Raises:
        FirebaseError: If there's an error accessing Firestore
    """
    logger.info(f"Getting budgets for user: {user_id}")
    try:
        # Query Firestore for all budgets matching user_id
        budgets_ref = db.collection("budgets").where("user_id", "==", user_id).stream()
        
        # Convert Firestore documents to Budget objects
        budgets = []
        for budget_doc in budgets_ref:
            budget_data = budget_doc.to_dict()
            try:
                budget = Budget(**budget_data)
                budgets.append(budget)
            except ValidationError as ve:
                logger.error(f"Error converting budget {budget_doc.id} to model: {ve}")
                continue
        
        logger.info(f"Successfully retrieved {len(budgets)} budgets for user {user_id}")
        return budgets
    
    except Exception as e:
        logger.error(f"Error fetching budgets for user {user_id}: {e}", exc_info=True)
        raise

# Account operations
def create_account(account: Account) -> Account:
    try:
        if not get_user(account.user_id):
            raise ValueError("User does not exist.")
        if not get_budget(account.budget_id):
            raise ValueError("Budget does not exist.")
        # Generate new document reference with auto ID
        account_ref = db.collection("accounts").document()
        # Assign the generated ID to the model
        account.account_id = account_ref.id
        # Save the data
        account_ref.set(account.dict())
        logger.info(f"Created account with ID: {account.account_id}")
        return account
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise

def get_account(account_id: str) -> Optional[Dict[str, Any]]:
    account_ref = db.collection("accounts").document(account_id).get()
    return account_ref.to_dict() if account_ref.exists else None

# Transaction operations
def create_transaction(transaction: Transaction) -> Transaction:
    try:
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
        
        # Generate new document reference with auto ID
        transaction_ref = db.collection("transactions").document()
        # Assign the generated ID to the model
        transaction.transaction_id = transaction_ref.id
        # Save the data
        transaction_ref.set(transaction.dict())
        logger.info(f"Created transaction with ID: {transaction.transaction_id}")
        return transaction
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise

def get_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
    transaction_ref = db.collection("transactions").document(transaction_id).get()
    return transaction_ref.to_dict() if transaction_ref.exists else None

# Recurring Transaction operations
def create_recurring_transaction(recurring_transaction: RecurringTransaction) -> RecurringTransaction:
    try:
        if not get_budget(recurring_transaction.budget_id):
            raise ValueError("Budget does not exist.")
        
        # Generate new document reference with auto ID
        recurring_ref = db.collection("recurringTransactions").document()
        # Assign the generated ID to the model
        recurring_transaction.recurring_id = recurring_ref.id
        # Save the data
        recurring_ref.set(recurring_transaction.dict())
        logger.info(f"Created recurring transaction with ID: {recurring_transaction.recurring_id}")
        return recurring_transaction
    except Exception as e:
        logger.error(f"Error creating recurring transaction: {e}")
        raise

def get_recurring_transaction(recurring_id: str) -> Optional[Dict[str, Any]]:
    recurring_ref = db.collection("recurringTransactions").document(recurring_id).get()
    return recurring_ref.to_dict() if recurring_ref.exists else None

# Currency operations
def update_currency_rates(currency: Currency) -> None:
    currency_ref = db.collection("currencies").document(currency.currency_code)
    currency_ref.set(currency.dict())

def get_currency_rate(currency_code: str) -> Optional[Dict[str, Any]]:
    currency_ref = db.collection("currencies").document(currency_code).get()
    return currency_ref.to_dict() if currency_ref.exists else None