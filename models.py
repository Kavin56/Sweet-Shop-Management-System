from pydantic import BaseModel
from typing import Optional

# User models
class UserRegister(BaseModel):
    username: str
    password: str
    admin_key: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Sweet models
class SweetCreate(BaseModel):
    name: str
    category: str
    price: float
    quantity: int

class SweetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None

class SweetResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    quantity: int
    created_at: str

    class Config:
        from_attributes = True

# Purchase/Restock models
class PurchaseRequest(BaseModel):
    quantity: int

class RestockRequest(BaseModel):
    quantity: int

# Search models
class SearchParams(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

