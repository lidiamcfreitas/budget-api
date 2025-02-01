from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

class BudgetItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    description: str
    amount: float
    date: datetime
    
class BudgetItemCreate(BaseModel):
    description: str
    amount: float
    date: datetime

class BudgetItemUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[datetime] = None

