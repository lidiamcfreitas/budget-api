import asyncio
from fastapi import FastAPI, HTTPException, status, Request, Depends, Path, Body
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List, Callable, Any
from uuid import UUID
import firebase_admin
from firebase_admin import auth, firestore, credentials
from models import User, Budget, CategoryGroup, Category
from services.account_service import AccountService
from services.budget_report_service import BudgetReportService
from services.category_groups_service import CategoryGroupsService
from services.category_service import CategoryService
from services.cross_budget_transfer_service import CrossBudgetTransferService
from services.currency_service import CurrencyService
from services.payee_service import PayeeService
from services.recurring_transaction_service import RecurringTransactionService
from services.transaction_service import TransactionService
from services.budget_service import BudgetService
from services.user_service import UserService
from routers import users #, budgets, categories, category_groups, reports

from firestore_service import (
    create_budget, get_budget, get_user_budgets,
    create_category_group, get_category_group, get_budget_category_groups,
    update_category_group, delete_category_group, get_monthly_budget_data,
    create_category
)
from utils import debug_request, get_token, handle_exceptions
from logger import logger

import functools

def create_app():
    app = FastAPI(
        title="Ignite - budget API",
        description="REST API for budget management",
        version="1.0.0"
    )
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
    #    allow_origins=["http://localhost:8080"],  # Vue.js development server
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
        expose_headers=["Content-Length"],
        max_age=600,
    )
    # Path to your Firebase service account key JSON file
    FIREBASE_CREDENTIALS_PATH = "/Users/lidiafreitas/programming/keys/budgetapp-449511-firebase-adminsdk-fbsvc-80fc508f2e.json"

    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            "projectId": "budgetapp-449511",
        })

    # Use the correct Firestore database
    db = firestore.client()


    # Include routers
    app.include_router(users.router)
    # app.include_router(budgets.router)
    # app.include_router(categories.router)
    # app.include_router(category_groups.router)
    # app.include_router(reports.router)
    
    return app, db

app, db = create_app()

# Create a dependency provider and add services' getters
def get_db():
    return firestore.client()

def get_account_service(db: firestore.Client = Depends(get_db)):
    return AccountService(db)

def get_budget_report_service(db: firestore.Client = Depends(get_db)):
    return BudgetReportService(db)

def get_budget_service(db: firestore.Client = Depends(get_db)):
    return BudgetService(db)

def get_category_group_service(db: firestore.Client = Depends(get_db)):
    return CategoryGroupsService(db)

def get_category_service(db: firestore.Client = Depends(get_db)):
    return CategoryService(db)

def get_cross_budget_transfer_service(db: firestore.Client = Depends(get_db)):
    return CrossBudgetTransferService(db)

def get_currency_service(db: firestore.Client = Depends(get_db)):
    return CurrencyService(db)

def get_payee_service(db: firestore.Client = Depends(get_db)):
    return PayeeService(db)

def get_recurring_transaction_service(db: firestore.Client = Depends(get_db)):
    return RecurringTransactionService(db)

def get_transaction_service(db: firestore.Client = Depends(get_db)):
    return TransactionService(db)


@app.get("/routes", tags=["Debug"])
async def list_routes():
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append({
                "path": route.path,
                "name": route.name,
                "methods": route.methods
            })
    return {"routes": routes}

# @app.post("/api/budgets", response_model=Budget)
# async def create_new_budget(request: Request, budget: Budget):
#     try:
#         debug_request(request)
#         token = get_token(request)
#         if not token:
#             raise HTTPException(status_code=401, detail="No token provided")
        
#         # Verify the Firebase ID token
#         decoded_token = auth.verify_id_token(token)
#         user_id = decoded_token['uid']
#         logger.info(f"Creating budget for user: {user_id}")

#         # Verify user exists
#         user = get_user(user_id)
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )
        
#         # Set the user_id in the budget
#         budget.user_id = user_id
        
#         # Create the budget
#         created_budget = create_budget(budget)
#         logger.info(f"Budget created successfully: {created_budget.budget_id}")
        
#         return created_budget
        
#     except Exception as e:
#         logger.error(f"Error creating budget: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

# @app.get("/api/budgets/{budget_id}", response_model=Budget)
# async def get_budget_by_id(request: Request, budget_id: str):
#     try:
#         token = get_token(request)
#         if not token:
#             raise HTTPException(status_code=401, detail="No token provided")
        
#         # Verify the Firebase ID token
#         decoded_token = auth.verify_id_token(token)
#         user_id = decoded_token['uid']
        
#         budget = get_budget(budget_id)
#         if not budget:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Budget not found"
#             )
        
#         # Verify user has access to this budget
#         if budget['user_id'] != user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Not authorized to access this budget"
#             )
        
#         return budget
        
#     except Exception as e:
#         logger.error(f"Error retrieving budget: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

# @app.get(
#     "/api/users/{user_id}/budgets",
#     response_model=List[Budget],
#     responses={
#         401: {"description": "Unauthorized - No token provided or invalid token"},
#         403: {"description": "Forbidden - User trying to access another user's budgets"},
#         404: {"description": "User not found"}
#     },
#     tags=["Budgets"],
#     summary="Get all budgets for a user",
#     description="Retrieves all budgets associated with a user. Budgets are returned in alphabetical order by name."
# )
# async def get_user_budgets_list(
#     request: Request,
#     user_id: str = Path(..., description="The ID of the user to get budgets for")
# ):
#     try:
#         token = get_token(request)
#         if not token:
#             raise HTTPException(status_code=401, detail="No token provided")
        
#         # Verify the Firebase ID token
#         decoded_token = auth.verify_id_token(token)
#         token_user_id = decoded_token['uid']
        
#         # Verify user can only access their own budgets
#         if user_id != token_user_id:
#             logger.warning(f"User {token_user_id} attempted to access budgets of user {user_id}")
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Not authorized to access these budgets"
#             )
        
#         # Verify user exists
#         user = get_user(user_id)
#         if not user:
#             logger.error(f"User {user_id} not found when attempting to retrieve budgets")
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )
        
#         budgets = get_user_budgets(user_id)
#         # Sort budgets alphabetically by name
#         budgets.sort(key=lambda x: x.name.lower())
        
#         logger.info(f"Retrieved and sorted {len(budgets)} budgets for user {user_id}")
        
#         return budgets
        
#     except Exception as e:
#         logger.error(f"Error retrieving user budgets: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
# @app.post(
#     "/api/budgets/{budget_id}/category-groups",
#     response_model=CategoryGroup,
#     responses={
#         401: {"description": "Unauthorized - No token provided or invalid token"},
#         403: {"description": "Forbidden - User doesn't have access to this budget"},
#         404: {"description": "Budget not found"}
#     },
#     tags=["Category Groups"],
#     summary="Create a new category group",
#     description="Creates a new category group within the specified budget."
# )
# async def create_new_category_group(
#     request: Request,
#     budget_id: str = Path(..., description="The ID of the budget to create the category group in"),
#     category_group: CategoryGroup = Body(..., description="The category group to create")
# ):
#     try:
#         logger.info(f"Creating new category group in budget {budget_id}")
#         logger.debug(f"Category group details: {category_group.dict()}")
        
#         token = get_token(request)
#         if not token:
#             logger.warning("No token provided in request")
#             raise HTTPException(status_code=401, detail="No token provided")
        
#         # Verify the Firebase ID token
#         decoded_token = auth.verify_id_token(token)
#         user_id = decoded_token['uid']
#         logger.debug(f"Token verified for user: {user_id}")
        
#         # Get the budget to verify access
#         logger.debug(f"Retrieving budget {budget_id}")
#         budget = get_budget(budget_id)
#         if not budget:
#             logger.warning(f"Budget {budget_id} not found")
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Budget not found"
#             )
#         logger.debug(f"Successfully retrieved budget: {budget_id}")
#         logger.debug(f"Budget: {budget}")
#         logger.debug(f"User ID: {user_id}")
#         # Verify user has access to this budget
#         if budget['user_id'] != user_id:
#             logger.warning(f"User {user_id} attempted to access unauthorized budget {budget_id}")
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Not authorized to access this budget"
#             )
#         logger.debug(f"Access verified for user {user_id} to budget {budget_id}")
        
#         # Set the budget_id in the category group
#         category_group.budget_id = budget_id
        
#         # Create the category group
#         logger.debug(f"Attempting to create category group: {category_group.name}")
#         created_group = create_category_group(category_group)
#         logger.info(f"Category group created successfully: {created_group.group_id} '{created_group.name}'")
        
#         return created_group
        
#     except Exception as e:
#         logger.error(f"Error creating category group: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

# @app.get(
#     "/api/budgets/{budget_id}/category-groups",
#     response_model=List[CategoryGroup],
#     responses={
#         401: {"description": "Unauthorized - No token provided or invalid token"},
#         403: {"description": "Forbidden - User doesn't have access to this budget"},
#         404: {"description": "Budget not found"}
#     },
#     tags=["Category Groups"],
#     summary="Get all category groups in a budget",
#     description="Retrieves all category groups associated with the specified budget."
# )
# async def get_budget_category_groups_list(
#     request: Request,
#     budget_id: str = Path(..., description="The ID of the budget to get category groups from")
# ):
#     try:
#         token = get_token(request)
#         if not token:
#             raise HTTPException(status_code=401, detail="No token provided")
        
#         # Verify the Firebase ID token
#         decoded_token = auth.verify_id_token(token)
#         user_id = decoded_token['uid']
        
#         # Get the budget to verify access
#         budget = get_budget(budget_id)
#         if not budget:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Budget not found"
#             )
        
#         # Verify user has access to this budget
#         if budget['user_id'] != user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Not authorized to access this budget"
#             )
        
#         category_groups = get_budget_category_groups(budget_id)
#         logger.info(f"Retrieved {len(category_groups)} category groups for budget {budget_id}")
        
#         return category_groups
        
#     except Exception as e:
#         logger.error(f"Error retrieving category groups: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

# @app.get(
#     "/api/category-groups/{group_id}",
#     response_model=CategoryGroup,
#     responses={
#         401: {"description": "Unauthorized - No token provided or invalid token"},
#         403: {"description": "Forbidden - User doesn't have access to this category group"},
#         404: {"description": "Category group not found"}
#     },
#     tags=["Category Groups"],
#     summary="Get a specific category group",
#     description="Retrieves details for a specific category group."
# )
# async def get_category_group_by_id(
#     request: Request,
#     group_id: str = Path(..., description="The ID of the category group to retrieve")
# ):
#     try:
#         token = get_token(request)
#         if not token:
#             raise HTTPException(status_code=401, detail="No token provided")
        
#         # Verify the Firebase ID token
#         decoded_token = auth.verify_id_token(token)
#         user_id = decoded_token['uid']
        
#         # Get the category group
#         category_group = get_category_group(group_id)
#         if not category_group:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Category group not found"
#             )
        
#         # Get the budget to verify access
#         budget = get_budget(category_group.budget_id)
#         if budget['user_id'] != user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Not authorized to access this category group"
#             )
        
#         return category_group
        
#     except Exception as e:
#         logger.error(f"Error retrieving category group: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

# @app.put(
#     "/api/category-groups/{group_id}",
#     response_model=CategoryGroup,
#     responses={
#         401: {"description": "Unauthorized - No token provided or invalid token"},
#         403: {"description": "Forbidden - User doesn't have access to this category group"},
#         404: {"description": "Category group not found"}
#     },
#     tags=["Category Groups"],
#     summary="Update a category group",
#     description="Updates an existing category group."
# )
# async def update_category_group_by_id(
#     request: Request,
#     group_id: str = Path(..., description="The ID of the category group to update"),
#     category_group: CategoryGroup = Body(..., description="The updated category group data")
# ):
#     try:
#         token = get_token(request)
#         if not token:
#             raise HTTPException(status_code=401, detail="No token provided")
        
#         # Verify the Firebase ID token
#         decoded_token = auth.verify_id_token(token)
#         user_id = decoded_token['uid']
        
#         # Get the existing category group
#         existing_group = get_category_group(group_id)
#         if not existing_group:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Category group not found"
#             )
        
#         # Get the budget to verify access
#         budget = get_budget(existing_group.budget_id)
#         if budget['user_id'] != user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Not authorized to access this category group"
#             )
        
#         # Update the category group
#         category_group.group_id = group_id
#         category_group.budget_id = existing_group.budget_id
#         updated_group = update_category_group(category_group)
#         logger.info(f"Category group updated successfully: {group_id}")
        
#         return updated_group
        
#     except Exception as e:
#         logger.error(f"Error updating category group: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

# @app.delete(
#     "/api/category-groups/{group_id}",
#     responses={
#         401: {"description": "Unauthorized - No token provided or invalid token"},
#         403: {"description": "Forbidden - User doesn't have access to this category group"},
#         404: {"description": "Category group not found"}
#     },
#     tags=["Category Groups"],
#     summary="Delete a category group",
#     description="Deletes an existing category group."
# )
# async def delete_category_group_by_id(
#     request: Request,
#     group_id: str = Path(..., description="The ID of the category group to delete")
# ):
#     try:
#         token = get_token(request)
#         if not token:
#             raise HTTPException(status_code=401, detail="No token provided")
        
#         # Verify the Firebase ID token
#         decoded_token = auth.verify_id_token(token)
#         user_id = decoded_token['uid']
        
#         # Get the category group
#         category_group = get_category_group(group_id)
#         if not category_group:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Category group not found"
#             )
        
#         # Get the budget to verify access
#         budget = get_budget(category_group.budget_id)
#         if budget['user_id'] != user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Not authorized to access this category group"
#             )
        
#         # Delete the category group
#         delete_category_group(group_id)
#         logger.info(f"Category group deleted successfully: {group_id}")
        
#         return {"message": "Category group deleted successfully"}
        
#     except Exception as e:
#         logger.error(f"Error deleting category group: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

# @app.post(
#     "/api/budgets/{budget_id}/category-groups/{group_id}/categories",
#     response_model=Category,
#     responses={
#         401: {"description": "Unauthorized - No token provided or invalid token"},
#         403: {"description": "Forbidden - User doesn't have access to this budget"},
#         404: {"description": "Budget or category group not found"}
#     },
#     tags=["Categories"],
#     summary="Create a new category",
#     description="Creates a new category within the specified budget and category group."
# )
# async def create_new_category(
#     request: Request,
#     budget_id: str = Path(..., description="The ID of the budget to create the category in"),
#     group_id: str = Path(..., description="The ID of the category group to create the category in"),
#     category_data: Category = Body(..., description="The category to create")
# ):
#     try:
#         logger.info(f"Creating new category in budget {budget_id} and group {group_id}")
        
#         token = get_token(request)
#         if not token:
#             logger.warning("No token provided in request")
#             raise HTTPException(status_code=401, detail="No token provided")
        
#         # Verify the Firebase ID token
#         decoded_token = auth.verify_id_token(token)
#         user_id = decoded_token['uid']
#         logger.debug(f"Token verified for user: {user_id}")
        
#         # Get the budget to verify access
#         budget = get_budget(budget_id)
#         if not budget:
#             logger.warning(f"Budget {budget_id} not found")
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Budget not found"
#             )
        
#         # Verify user has access to this budget
#         if budget['user_id'] != user_id:
#             logger.warning(f"User {user_id} attempted to access unauthorized budget {budget_id}")
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Not authorized to access this budget"
#             )

#         # Verify category group exists
#         category_group = get_category_group(category_data.group_id)
#         if not category_group:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Category group not found"
#             )
#         category_data.group_id = group_id
        
#         new_category = create_category(category_data)
#         logger.info(f"Category created successfully: {new_category.category_id}")
        
#         return new_category
        
#     except Exception as e:
#         logger.error(f"Error creating category: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

# @app.get(
#     "/api/budgets/{budget_id}/monthly-data/{month}",
#     responses={
#         401: {"description": "Unauthorized - No token provided or invalid token"},
#         403: {"description": "Forbidden - User doesn't have access to this budget"},
#         404: {"description": "Budget not found"},
#         422: {"description": "Invalid month format - must be YYYY-MM"}
#     },
#     tags=["Budgets"],
#     summary="Get monthly budget data",
#     description="Retrieves monthly budget data including transactions and budget amounts for the specified month."
# )
# async def get_budget_monthly_data(
#     request: Request,
#     budget_id: str = Path(..., description="The ID of the budget to get monthly data for"),
#     month: str = Path(..., description="The month to get data for in format YYYY-MM")
# ):
#     try:
#         logger.info(f"Fetching monthly data for budget {budget_id} for month {month}")
        
#         # Validate month format
#         try:
#             datetime.strptime(month, "%Y-%m")
#         except ValueError:
#             logger.warning(f"Invalid month format provided: {month}")
#             raise HTTPException(
#                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#                 detail="Invalid month format. Must be YYYY-MM"
#             )
        
#         token = get_token(request)
#         if not token:
#             logger.warning("No token provided in request")
#             raise HTTPException(status_code=401, detail="No token provided")
        
#         # Verify the Firebase ID token
#         decoded_token = auth.verify_id_token(token)
#         user_id = decoded_token['uid']
#         logger.debug(f"Token verified for user: {user_id}")
        
#         # Get the budget to verify access
#         logger.debug(f"Retrieving budget {budget_id}")
#         budget = get_budget(budget_id)
#         if not budget:
#             logger.warning(f"Budget {budget_id} not found")
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Budget not found"
#             )
        
#         # Verify user has access to this budget
#         if budget['user_id'] != user_id:
#             logger.warning(f"User {user_id} attempted to access unauthorized budget {budget_id}")
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Not authorized to access this budget"
#             )
        
#         # Get monthly data
#         logger.debug(f"Fetching monthly data for budget {budget_id} month {month}")
#         monthly_data = get_monthly_budget_data(budget_id, month)
#         logger.info(f"Successfully retrieved monthly data for budget {budget_id} month {month}")
        
#         return monthly_data
        
#     except Exception as e:
#         logger.error(f"Error retrieving monthly budget data: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
