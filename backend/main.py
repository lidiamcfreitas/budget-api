from fastapi import FastAPI, HTTPException, status, Request
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from uuid import UUID

from models import BudgetItem, BudgetItemCreate, BudgetItemUpdate, NameRequest
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

# In-memory storage for budget items
budget_items: List[BudgetItem] = []

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

@app.post("/budget", response_model=BudgetItem, status_code=status.HTTP_201_CREATED)
async def create_budget_item(item: BudgetItemCreate):
    budget_item = BudgetItem(**item.dict())
    budget_items.append(budget_item)
    return budget_item

@app.get("/budget", response_model=List[BudgetItem])
async def list_budget_items():
    return budget_items

@app.get("/budget/{item_id}", response_model=BudgetItem)
async def get_budget_item(item_id: UUID):
    for item in budget_items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Budget item not found")

@app.put("/budget/{item_id}", response_model=BudgetItem)
async def update_budget_item(item_id: UUID, item: BudgetItemUpdate):
    for budget_item in budget_items:
        if budget_item.id == item_id:
            update_data = item.dict(exclude_unset=True)
            return budget_item.copy(update=update_data)
    raise HTTPException(status_code=404, detail="Budget item not found")

@app.delete("/budget/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget_item(item_id: UUID):
    for idx, item in enumerate(budget_items):
        if item.id == item_id:
            budget_items.pop(idx)
            return
    raise HTTPException(status_code=404, detail="Budget item not found")

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
