from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserOut(BaseModel):
    id : int
    userName : str
    email : EmailStr
    firstName : Optional[str] = Field(None)
    lastName : Optional[str] = Field(None)
    created_at : Optional[datetime] = Field(None, alias="createdAt")
    updated_at : Optional[datetime] = Field(None, alias="updatedAt")

    class Config:
        validate_by_name = True  # Accept snake_case or camelCase
        from_attributes = True

class UserCreate(BaseModel):
    userName : str
    email : EmailStr
    password : str
    firstName : Optional[str] = Field(None)
    lastName : Optional[str] = Field(None)

    class Config:
        from_attributes = True
        validate_by_name = True
    

class Team(BaseModel):
    id : int
    name : str
    short_name : str 
    logo_url : Optional[str]

class UpdateUser(BaseModel):
    userName : Optional[str] = None
    firstName : Optional[str] = None
    lastName : Optional[str] = None
    email : Optional[str] = None
    password : Optional[str] = None
    created_at : Optional[str] = None
    updated_at : Optional[str] = None

    class Config:
        validate_by_name = True
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str
