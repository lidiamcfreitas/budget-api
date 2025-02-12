import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Optional, Dict, Any
from models import User, Budget, Account, Transaction, RecurringTransaction, Currency, CategoryGroup, Category
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)  # Use a named logger

# Path to your Firebase service account key JSON file
FIREBASE_CREDENTIALS_PATH = "/Users/lidiafreitas/programming/keys/budgetapp-449511-firebase-adminsdk-fbsvc-80fc508f2e.json"

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {
        "projectId": "budgetapp-449511",
    })

# Use the correct Firestore database
db = firestore.client()

# # User operations
# def create_user(user: User) -> None:
#     logger.debug(f"Creating user with ID: {user.user_id}")
#     if get_user(user.user_id):
#         logger.debug(f"User {user.user_id} already exists")
#         raise ValueError("User already exists.")
#     user_ref = db.collection("users").document(user.user_id)
#     logger.debug(f"Setting user data: {user.dict()}")
#     user_ref.set(user.dict())
#     logger.info(f"Successfully created user: {user.user_id}")

# def get_user(user_id: str) -> Optional[Dict[str, Any]]:
#     logger.debug(f"Getting user with ID: {user_id}")
#     try:
#         logger.debug("Querying Firestore for user document")
#         user_ref = db.collection("users").document(user_id).get()
        
#         if user_ref.exists:
#             user_data = user_ref.to_dict()
#             logger.debug(f"Found user data: {user_data}")
#             logger.info(f"Successfully retrieved user: {user_id}")
#             return user_data
#         else:
#             logger.debug(f"No user found with ID: {user_id}")
#             return None
            
#     except Exception as e:
#         logger.error(f"Error getting user: {e}")
#         return None

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
    logger.debug(f"Getting budget with ID: {budget_id}")
    try:
        logger.debug("Querying Firestore for budget document")
        budget_ref = db.collection("budgets").document(budget_id).get()
        
        if budget_ref.exists:
            budget_data = budget_ref.to_dict()
            logger.debug(f"Found budget data: {budget_data}")
            logger.info(f"Successfully retrieved budget: {budget_id}")
            return budget_data
        else:
            logger.debug(f"No budget found with ID: {budget_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting budget: {e}")
        return None

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
    logger.debug(f"Getting account with ID: {account_id}")
    try:
        logger.debug("Querying Firestore for account document")
        account_ref = db.collection("accounts").document(account_id).get()
        
        if account_ref.exists:
            account_data = account_ref.to_dict()
            logger.debug(f"Found account data: {account_data}")
            logger.info(f"Successfully retrieved account: {account_id}")
            return account_data
        else:
            logger.debug(f"No account found with ID: {account_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting account: {e}")
        return None

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
    logger.debug(f"Getting transaction with ID: {transaction_id}")
    try:
        logger.debug("Querying Firestore for transaction document")
        transaction_ref = db.collection("transactions").document(transaction_id).get()
        
        if transaction_ref.exists:
            transaction_data = transaction_ref.to_dict()
            logger.debug(f"Found transaction data: {transaction_data}")
            logger.info(f"Successfully retrieved transaction: {transaction_id}")
            return transaction_data
        else:
            logger.debug(f"No transaction found with ID: {transaction_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting transaction: {e}")
        return None

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
    logger.debug(f"Updating currency rates for {currency.currency_code}")
    try:
        logger.debug(f"Currency data: {currency.dict()}")
        currency_ref = db.collection("currencies").document(currency.currency_code)
        currency_ref.set(currency.dict())
        logger.info(f"Successfully updated currency rates for {currency.currency_code}")
    except Exception as e:
        logger.error(f"Error updating currency rates: {e}")
        raise

def get_currency_rate(currency_code: str) -> Optional[Dict[str, Any]]:
    logger.debug(f"Getting currency rate for {currency_code}")
    try:
        logger.debug("Querying Firestore for currency document")
        currency_ref = db.collection("currencies").document(currency_code).get()
        
        if currency_ref.exists:
            currency_data = currency_ref.to_dict()
            logger.debug(f"Found currency data: {currency_data}")
            logger.info(f"Successfully retrieved currency rate for {currency_code}")
            return currency_data
        else:
            logger.debug(f"No currency rate found for {currency_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting currency rate: {e}")
        return None

# Category Group operations
def create_category_group(category_group: CategoryGroup) -> CategoryGroup:
    """
    Create a new category group in Firestore.
    
    Args:
        category_group (CategoryGroup): The category group to create
        
    Returns:
        CategoryGroup: The created category group with assigned ID
        
    Raises:
        ValueError: If the user or budget doesn't exist
    """
    try:
        if not get_user(category_group.user_id):
            raise ValueError("User does not exist.")
        if not get_budget(category_group.budget_id):
            raise ValueError("Budget does not exist.")
        
        # Generate new document reference with auto ID
        group_ref = db.collection("categoryGroups").document()
        # Assign the generated ID to the model
        category_group.group_id = group_ref.id
        # Save the data
        group_ref.set(category_group.dict())
        logger.info(f"Created category group with ID: {category_group.group_id}")
        return category_group
    except Exception as e:
        logger.error(f"Error creating category group: {e}")
        raise

def get_category_group(group_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a category group by its ID.
    
    Args:
        group_id (str): The ID of the category group to retrieve
        
    Returns:
        Optional[Dict[str, Any]]: The category group data if found, None otherwise
    """
    try:
        group_ref = db.collection("categoryGroups").document(group_id).get()
        return group_ref.to_dict() if group_ref.exists else None
    except Exception as e:
        logger.error(f"Error getting category group {group_id}: {e}")
        return None

def get_budget_category_groups(budget_id: str) -> List[CategoryGroup]:
    """
    Retrieve all category groups for a specific budget.
    
    Args:
        budget_id (str): The ID of the budget
        
    Returns:
        List[CategoryGroup]: List of category groups belonging to the budget
    """
    try:
        groups_ref = db.collection("categoryGroups").where("budget_id", "==", budget_id).stream()
        
        category_groups = []
        for group_doc in groups_ref:
            group_data = group_doc.to_dict()
            try:
                group = CategoryGroup(**group_data)
                category_groups.append(group)
            except ValidationError as ve:
                logger.error(f"Error converting category group {group_doc.id} to model: {ve}")
                continue
        
        logger.info(f"Retrieved {len(category_groups)} category groups for budget {budget_id}")
        return category_groups
    
    except Exception as e:
        logger.error(f"Error fetching category groups for budget {budget_id}: {e}")
        raise

def update_category_group(group_id: str, updated_data: Dict[str, Any]) -> None:
    """
    Update a category group's data.
    
    Args:
        group_id (str): The ID of the category group to update
        updated_data (Dict[str, Any]): The new data to update
    """
    try:
        group_ref = db.collection("categoryGroups").document(group_id)
        group_ref.update(updated_data)
        logger.info(f"Updated category group: {group_id}")
    except Exception as e:
        logger.error(f"Error updating category group {group_id}: {e}")
        raise

def delete_category_group(group_id: str) -> None:
    """
    Delete a category group.
    
    Args:
        group_id (str): The ID of the category group to delete
    """
    try:
        group_ref = db.collection("categoryGroups").document(group_id)
        group_ref.delete()
        logger.info(f"Deleted category group: {group_id}")
    except Exception as e:
        logger.error(f"Error deleting category group {group_id}: {e}")
        raise

# Category operations
def create_category(category: Category) -> Category:
    """
    Create a new category in Firestore.
    
    Args:
        category (Category): The category to create
        
    Returns:
        Category: The created category with assigned ID
        
    Raises:
        ValueError: If the group doesn't exist
    """
    try:
        if not get_category_group(category.group_id):
            raise ValueError("Category group does not exist.")
        
        # Generate new document reference with auto ID
        category_ref = db.collection("categories").document()
        # Assign the generated ID to the model
        category.category_id = category_ref.id
        # Save the data
        category_ref.set(category.dict())
        logger.info(f"Created category with ID: {category.category_id}")
        return category
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        raise

def get_category(category_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a category by its ID.
    
    Args:
        category_id (str): The ID of the category to retrieve
        
    Returns:
        Optional[Dict[str, Any]]: The category data if found, None otherwise
    """
    try:
        category_ref = db.collection("categories").document(category_id).get()
        return category_ref.to_dict() if category_ref.exists else None
    except Exception as e:
        logger.error(f"Error getting category {category_id}: {e}")
        return None

def get_group_categories(group_id: str) -> List[Category]:
    """
    Retrieve all categories for a specific category group.
    
    Args:
        group_id (str): The ID of the category group
        
    Returns:
        List[Category]: List of categories belonging to the group
    """
    try:
        categories_ref = db.collection("categories").where("group_id", "==", group_id).stream()
        
        categories = []
        for category_doc in categories_ref:
            category_data = category_doc.to_dict()
            try:
                category = Category(**category_data)
                categories.append(category)
            except ValidationError as ve:
                logger.error(f"Error converting category {category_doc.id} to model: {ve}")
                continue
        
        logger.info(f"Retrieved {len(categories)} categories for group {group_id}")
        return categories
    
    except Exception as e:
        logger.error(f"Error fetching categories for group {group_id}: {e}")
        raise

def update_category(category_id: str, updated_data: Dict[str, Any]) -> None:
    """
    Update a category's data.
    
    Args:
        category_id (str): The ID of the category to update
        updated_data (Dict[str, Any]): The new data to update
    """
    try:
        category_ref = db.collection("categories").document(category_id)
        category_ref.update(updated_data)
        logger.info(f"Updated category: {category_id}")
    except Exception as e:
        logger.error(f"Error updating category {category_id}: {e}")
        raise

def delete_category(category_id: str) -> None:
    """
    Delete a category.
    
    Args:
        category_id (str): The ID of the category to delete
    """
    try:
        category_ref = db.collection("categories").document(category_id)
        category_ref.delete()
        logger.info(f"Deleted category: {category_id}")
    except Exception as e:
        logger.error(f"Error deleting category {category_id}: {e}")
        raise

def get_monthly_budget_data(budget_id: str, month: str) -> Dict[str, Any]:
    """
    Get monthly budget data including transactions and category totals.
    
    Args:
        budget_id (str): The ID of the budget
        month (str): The month in YYYY-MM format
        
    Returns:
        Dict[str, Any]: Monthly budget data including:
            - category_groups: List of category groups with their categories
            - transactions: List of transactions for the month
            - totals: Monthly totals and category-wise totals
    """
    try:
        logger.info(f"Fetching monthly data for budget {budget_id} month {month}")
        
        # Get start and end dates for the month
        start_date = f"{month}-01"
        next_month = f"{month}-01"
        if month.endswith("12"):
            next_month = f"{int(month[:4]) + 1}-01-01"
        else:
            next_month = f"{month[:4]}-{int(month[5:7]) + 1:02d}-01"
        
        # Get transactions for the month
        transactions_ref = (
            db.collection("transactions")
            .where("budget_id", "==", budget_id)
            .where("date", ">=", start_date)
            .where("date", "<", next_month)
            .stream()
        )
        
        transactions = []
        category_totals = {}
        monthly_total = 0
        
        for trans_doc in transactions_ref:
            trans_data = trans_doc.to_dict()
            transactions.append(trans_data)
            
            # Calculate totals
            amount = trans_data.get("amount", 0)
            category_id = trans_data.get("category_id")
            if category_id:
                category_totals[category_id] = category_totals.get(category_id, 0) + amount
            monthly_total += amount
        
        # Get category groups and their categories
        category_groups = get_budget_category_groups(budget_id)
        groups_with_categories = []
        
        for group in category_groups:
            group_dict = group.dict()
            # Get categories for this group
            categories = get_group_categories(group.group_id)
            group_dict['categories'] = [cat.dict() for cat in categories]
            groups_with_categories.append(group_dict)
        
        # Structure the response
        response = {
            "month": month,
            "budget_id": budget_id,
            "category_groups": groups_with_categories,
            "transactions": transactions,
            "totals": {
                "monthly_total": monthly_total,
                "category_totals": category_totals
            }
        }
        
        logger.info(f"Successfully retrieved monthly data for budget {budget_id} month {month}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting monthly budget data: {e}")
        raise
