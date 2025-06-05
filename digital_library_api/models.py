from pydantic import BaseModel, Field, field_validator, ValidationInfo, ConfigDict
from datetime import date, timedelta, datetime
from typing import List, Optional, Dict, Any

# --- Pydantic Models ---
# Pydantic models remain largely the same, but BookInDB.id will change


# User Models
class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


# Pydantic models from original file, with modifications
class BookBase(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    isbn: str = Field(..., min_length=1, max_length=13)
    is_borrowed: bool = False
    # borrower_name: Optional[str] = None # Removed
    due_date: Optional[date] = None

    @field_validator("due_date", mode="before")  # Removed "borrower_name"
    @classmethod
    def check_borrow_details(cls, v: Any, info: ValidationInfo):
        is_borrowed = info.data.get("is_borrowed")

        if info.field_name == "due_date" and is_borrowed and v is None:
            raise ValueError("due_date is required if book is borrowed")
        # Removed borrower_name validation part
        if not is_borrowed and v is not None and info.field_name == "due_date":
            # If not borrowed, due_date should be None.
            # This will be enforced by endpoint logic primarily.
            # For validation, we can accept it but it might be cleared.
            pass
        return v


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):  # Changed to BaseModel for more explicit optional fields
    title: Optional[str] = Field(default=None, min_length=1)
    author: Optional[str] = Field(default=None, min_length=1)
    isbn: Optional[str] = Field(default=None, min_length=10, max_length=13)
    is_borrowed: Optional[bool] = Field(default=None)
    # borrower_name: Optional[str] = Field(default=None) # Removed
    due_date: Optional[date] = Field(default=None)


class BookInDB(BookBase):
    id: int = Field(...)
    borrower_id: Optional[int] = None
    borrower_username: Optional[str] = None  # Added to show who borrowed

    model_config = ConfigDict(from_attributes=True)


class User(UserBase):  # For API response
    id: int

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
