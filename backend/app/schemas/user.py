from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(..., max_length=50)
    password: str = Field(..., min_length=6)
    phone: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Login(BaseModel):
    username: str
    password: str
