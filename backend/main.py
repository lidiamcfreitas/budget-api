from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from uuid import UUID
from models import User, NameRequest
from firestore_service import create_user, get_user
from firebase_admin import auth

app = FastAPI(
    title="Budget API",
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

@app.post("/greet")
async def greet(request: NameRequest):
    return f"Hi {request.name}!"

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Budget API. This tests the github CI/CD.",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.post("/api/users", response_model=User)
async def register_user(id_token: str):
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        
        # Check if user already exists
        existing_user = get_user(user_id)
        if existing_user:
            return existing_user
        
        # Create new user
        new_user = User(
            user_id=user_id,
            email=decoded_token.get('email', ''),
        )
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
