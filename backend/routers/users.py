from fastapi import APIRouter, Depends, HTTPException, Request, status, Path, Body
from firebase_admin import auth, firestore
from typing import List
from models import User
from services.user_service import UserService
from utils import get_token, debug_request, handle_exceptions

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
    responses={401: {"description": "Unauthorized"}}
)

# Create a dependency provider and add services' getters
def get_db():
    return firestore.client()

def get_user_service(db: firestore.Client = Depends(get_db)):
    return UserService(db)


@router.post("", response_model=User)
@handle_exceptions("Error creating user")
async def register_user(
    request: Request,
    user: User,
    user_service: UserService = Depends(get_user_service)
):
    debug_request(request)
    user_service.verify_user(request)
    return await user_service.create_user(user)


@router.get("/{user_id}", response_model=User)
@handle_exceptions("Error getting user")
async def get_user_data(
    request: Request,
    user_id: str,
    user_service: UserService = Depends(get_user_service),
):
    user_service.verify_user(request)
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=User)
@handle_exceptions("Error updating user")
async def update_user(
    request: Request,
    user_id: str = Path(..., description="The ID of the user to update"),
    user_update: User = Body(..., description="Updated user information"),
    user_service: UserService = Depends(get_user_service)
):
    user_service.verify_user(request)
    # Verify user exists
    existing_user = await user_service.get_user(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify the requesting user has permission to update this user
    token = get_token(request)
    decoded_token = auth.verify_id_token(token)
    if decoded_token['uid'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    update_data = user_update.dict(exclude_unset=True)
    updated_user = await user_service.update_user(user_id, update_data)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_exceptions("Error deleting user")
async def delete_user(
    request: Request,
    user_id: str = Path(..., description="The ID of the user to delete"),
    user_service: UserService = Depends(get_user_service)
):
    user_service.verify_user(request)
    # Verify user exists
    existing_user = await user_service.get_user(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify the requesting user has permission to delete this user
    token = get_token(request)
    decoded_token = auth.verify_id_token(token)
    if decoded_token['uid'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )
    
    await user_service.delete_user(user_id)
    return None

