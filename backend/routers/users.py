from fastapi import APIRouter, Depends, Request, status, Path, Body, HTTPException
from firebase_admin import firestore
from typing import List
from models import User
from services.user_service import UserService
from utils import assert_user_matches, get_token, debug_request, handle_exceptions, maybe_throw_not_found

route = "users"
Service = UserService
Model = User

router = APIRouter(
    prefix=f"/api/{route}",
    tags=[route.capitalize()],
    responses={401: {"description": "Unauthorized"}}
)

# Create a dependency provider and add services' getters
def get_db():
    return firestore.client()

def get_service(db: firestore.Client = Depends(get_db)):
    return Service(db)


@router.post("", response_model=Model)
@handle_exceptions(f"Error creating {route}")
async def create(
    request: Request,
    doc: Model,
    service: Service = Depends(get_service)
):
    assert doc.id is not None, "ID is required"
    try:
        debug_request(request)
        return await service.create(request, doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{id}", response_model=Model)
@handle_exceptions(f"Error getting {route}")
async def get(
    request: Request,
    id: str,
    service: Service = Depends(get_service),
):
    try:
        assert_user_matches(request, id)
        doc = await service.get(request, id)
        maybe_throw_not_found(doc, f"{route} not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return doc


@router.put("/{id}", response_model=Model)
@handle_exceptions(f"Error updating {route}")
async def update(
    request: Request,
    id: str = Path(..., description="The ID of the doc to update"),
    doc_update: User = Body(..., description="Updated doc information"),
    service: Service = Depends(get_service)
):
    try:
        # Verify doc exists
        existing_doc = await service.get(request, id)
        maybe_throw_not_found(existing_doc, f"Doc in {route} not found")
        
        # Verify the requesting user has permission to update this doc
        assert_user_matches(request, id)

        update_data = doc_update.dict(exclude_unset=True)
        updated_doc = await service.update(request, id, update_data)
        return updated_doc
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_exceptions("Error deleting doc")
async def delete_user(
    request: Request,
    id: str = Path(..., description="The ID of the doc to delete"),
    service: Service = Depends(get_service)
):
    try:
        existing_doc = await service.get(request, id)
        maybe_throw_not_found(existing_doc, f"Doc in {route} not found")
        
        # Verify the requesting user has permission to delete this doc
        assert_user_matches(request, id)

        await service.delete(request, id)
        return None
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

