from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from uuid import UUID
from models import User, Budget
from firestore_service import create_user, get_user, create_budget, get_budget, get_user_budgets
from firebase_admin import auth
import logging
from utils import debug_request, get_token

app = FastAPI(
    title="Budget API",
    description="REST API for budget management",
    version="1.0.0"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more details
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)  # Use a named logger

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

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Budget API. This tests the github CI/CD.",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.post("/api/users", response_model=User)
async def register_user(request: Request):
    try:
        debug_request(request)
        token = get_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        logger.info(f"Decoded user ID: {user_id}")

        # Check if user already exists
        logger.info("Checking if user exists...")
        existing_user = get_user(user_id)
        logger.info("User exists" if existing_user else "User does not exist")
        if existing_user:
            logger.info("User already exists")
            return existing_user
        logger.info("Creating new user")
        try:
            # Create new user
            new_user = User(
                user_id=user_id,
                email=decoded_token.get('email', ''),
            )
            logger.info("Creating new user...")
        
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e))
        create_user(new_user)

        return new_user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/api/users/{user_id}", response_model=User)
async def get_user_data(user_id: str):
    user = get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

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

@app.post("/api/budgets", response_model=Budget)
async def create_new_budget(request: Request, budget: Budget):
    try:
        debug_request(request)
        token = get_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        logger.info(f"Creating budget for user: {user_id}")

        # Verify user exists
        user = get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Set the user_id in the budget
        budget.user_id = user_id
        
        # Create the budget
        created_budget = create_budget(budget)
        logger.info(f"Budget created successfully: {created_budget.budget_id}")
        
        return created_budget
        
    except Exception as e:
        logger.error(f"Error creating budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/api/budgets/{budget_id}", response_model=Budget)
async def get_budget_by_id(request: Request, budget_id: str):
    try:
        token = get_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        
        budget = get_budget(budget_id)
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found"
            )
        
        # Verify user has access to this budget
        if budget.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this budget"
            )
        
        return budget
        
    except Exception as e:
        logger.error(f"Error retrieving budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/api/users/{user_id}/budgets", response_model=List[Budget])
async def get_user_budgets_list(request: Request, user_id: str):
    try:
        token = get_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        token_user_id = decoded_token['uid']
        
        # Verify user can only access their own budgets
        if user_id != token_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access these budgets"
            )
        
        # Verify user exists
        user = get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        budgets = get_user_budgets(user_id)
        logger.info(f"Retrieved {len(budgets)} budgets for user {user_id}")
        
        return budgets
        
    except Exception as e:
        logger.error(f"Error retrieving user budgets: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
