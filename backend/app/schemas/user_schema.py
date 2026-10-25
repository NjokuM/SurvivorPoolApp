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

class UpdateProfileRequest(BaseModel):
    """PATCH /users/me - only the fields sent are changed."""
    userName: Optional[str] = Field(None, min_length=1, max_length=30)
    email: Optional[EmailStr] = None
    firstName: Optional[str] = Field(None, max_length=50)
    lastName: Optional[str] = Field(None, max_length=50)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8)


class GoogleAuthRequest(BaseModel):
    id_token: str


class AppleAuthRequest(BaseModel):
    identity_token: str
    # Apple only includes these on the user's very first authorization ever -
    # subsequent sign-ins omit them from both the client result and the
    # token, so the client passes along whatever it got (possibly nothing).
    email: Optional[EmailStr] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
