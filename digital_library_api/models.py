from pydantic import BaseModel, Field, field_validator, ValidationInfo
from datetime import date, timedelta, datetime
from typing import List, Optional, Dict, Any

# --- Pydantic Models ---
# Pydantic models remain largely the same, but BookInDB.id will change


class BookBase(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    isbn: str = Field(..., min_length=1, max_length=13)  # Basic ISBN length validation
    is_borrowed: bool = False
    borrower_name: Optional[str] = None
    due_date: Optional[date] = None

    @field_validator("due_date", "borrower_name", mode="before")
    @classmethod
    def check_borrow_details(cls, v: Any, info: ValidationInfo):
        # In V1, 'values' (a dict of other raw field values for pre=True) was a separate parameter.
        # In V2 @field_validator(mode='before'), all raw input data is in info.data.
        is_borrowed = info.data.get("is_borrowed")

        # 'info.field_name' correctly refers to the name of the field being validated ("due_date" or "borrower_name")
        if info.field_name == "due_date" and is_borrowed and v is None:
            raise ValueError("due_date is required if book is borrowed")
        if (
            info.field_name == "borrower_name"
            and is_borrowed
            and (v is None or not v.strip())
        ):
            raise ValueError(
                "borrower_name is required and cannot be empty if book is borrowed"
            )
        if not is_borrowed and v is not None:
            # If not borrowed, these fields should ideally be None,
            # but we can also choose to clear them in the logic.
            # For now, let's allow them to be set but they won't mean much.
            pass
        return v


class BookCreate(BookBase):
    pass


class BookUpdate(BookBase):
    # All fields are optional for partial updates.
    # We inherit from BookBase but override fields to be Optional.
    # A more explicit way is to redefine all fields:
    # class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    author: Optional[str] = Field(default=None, min_length=1)
    isbn: Optional[str] = Field(default=None, min_length=10, max_length=13)
    is_borrowed: Optional[bool] = Field(default=None)
    borrower_name: Optional[str] = Field(default=None)  # Allow explicit None to clear
    due_date: Optional[date] = Field(default=None)


class BookInDB(BookBase):
    id: int = Field(...)  # Changed from UUID to int

    class Config:
        from_attributes = True  # Replaces orm_mode = True for Pydantic v2
