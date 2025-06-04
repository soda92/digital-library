# c:\src\digital-library\digital_library\json_api.py
from datetime import date, timedelta, datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, status, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from sqlalchemy.orm import Session

from .database import SessionLocal, Book as DBBook, create_db_tables

# --- Configuration ---
# JSON_DB_FILE and DB_LOCK are no longer needed

# --- Pydantic Models ---
# Pydantic models remain largely the same, but BookInDB.id will change

class BookBase(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    isbn: str = Field(..., min_length=1, max_length=13) # Basic ISBN length validation
    is_borrowed: bool = False
    borrower_name: Optional[str] = None
    due_date: Optional[date] = None

    @field_validator("due_date", "borrower_name", mode='before')
    @classmethod
    def check_borrow_details(cls, v: Any, info: ValidationInfo):
        # In V1, 'values' (a dict of other raw field values for pre=True) was a separate parameter.
        # In V2 @field_validator(mode='before'), all raw input data is in info.data.
        is_borrowed = info.data.get("is_borrowed")

        # 'info.field_name' correctly refers to the name of the field being validated ("due_date" or "borrower_name")
        if info.field_name == "due_date" and is_borrowed and v is None:
            raise ValueError("due_date is required if book is borrowed")
        if info.field_name == "borrower_name" and is_borrowed and (v is None or not v.strip()):
            raise ValueError("borrower_name is required and cannot be empty if book is borrowed")
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
    borrower_name: Optional[str] = Field(default=None) # Allow explicit None to clear
    due_date: Optional[date] = Field(default=None)

class BookInDB(BookBase):
    id: int = Field(...) # Changed from UUID to int

    class Config:
        from_attributes = True # Replaces orm_mode = True for Pydantic v2

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FastAPI App ---
app = FastAPI(title="Digital Library JSON API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for simplicity, restrict in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    # Ensure database tables are created
    create_db_tables()
    print(f"SQLite Database API started. Using database: {SessionLocal().bind.url}")

# --- API Endpoints ---

@app.post("/books/", response_model=BookInDB, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate, db: Session = Depends(get_db)):
    # Check for ISBN uniqueness
    existing_book = db.query(DBBook).filter(DBBook.isbn == book.isbn).first()
    if existing_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book with ISBN {book.isbn} already exists.",
        )

    db_book = DBBook(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.get("/books/", response_model=List[BookInDB])
async def get_all_books(db: Session = Depends(get_db)):
    books = db.query(DBBook).all()
    return books

@app.get("/books/{book_id}", response_model=BookInDB) # book_id is now int
async def get_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return db_book

@app.put("/books/{book_id}", response_model=BookInDB) # book_id is now int
async def update_book(book_id: int, book_update: BookUpdate, db: Session = Depends(get_db)):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    update_data = book_update.model_dump(exclude_unset=True)

    # Check for ISBN uniqueness if ISBN is being changed
    if "isbn" in update_data and update_data["isbn"] != db_book.isbn:
        existing_book = db.query(DBBook).filter(DBBook.isbn == update_data["isbn"], DBBook.id != book_id).first()
        if existing_book:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another book with ISBN {update_data['isbn']} already exists.",
            )

    # Create a dictionary of the current book state to merge with updates
    current_book_data = BookInDB.model_validate(db_book).model_dump()
    proposed_data = current_book_data.copy()
    proposed_data.update(update_data)

    # If is_borrowed is explicitly set to False in the update, clear borrower details
    if "is_borrowed" in update_data and update_data["is_borrowed"] is False:
        proposed_data["borrower_name"] = None
        proposed_data["due_date"] = None
    
    # Validate the entire proposed state using BookBase logic
    try:
        validated_for_save = BookBase(**proposed_data)
    except ValueError as e: # Catches validation errors from BookBase's validator
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Apply validated updates to the SQLAlchemy model instance
    for key, value in validated_for_save.model_dump().items():
        setattr(db_book, key, value)
    
    # Specific check: if is_borrowed is true, ensure borrower_name and due_date are set
    # This should be covered by BookBase validation, but an explicit check after merge is safer
    if db_book.is_borrowed and (not db_book.borrower_name or not db_book.due_date):
        raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="If setting is_borrowed to true, borrower_name and due_date are required."
                )
    
    db.commit()
    db.refresh(db_book)
    return db_book

@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT) # book_id is now int
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    db.delete(db_book)
    db.commit()
    return None

@app.post("/books/{book_id}/borrow", response_model=BookInDB) # book_id is now int
async def borrow_book_action(
    book_id: int,
    borrower_name: str = Body(..., embed=True, min_length=1),
    borrow_days: int = Body(14, embed=True, gt=0),
    db: Session = Depends(get_db)
):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if db_book.is_borrowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book is already borrowed by {db_book.borrower_name}",
        )

    db_book.is_borrowed = True
    db_book.borrower_name = borrower_name
    db_book.due_date = date.today() + timedelta(days=borrow_days)
    
    db.commit()
    db.refresh(db_book)
    return db_book

@app.post("/books/{book_id}/return", response_model=BookInDB) # book_id is now int
async def return_book_action(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if not db_book.is_borrowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Book is not currently borrowed"
        )

    db_book.is_borrowed = False
    db_book.borrower_name = None
    db_book.due_date = None
    
    db.commit()
    db.refresh(db_book)
    return db_book

# To run this API (save as json_api.py):
# 1. Install FastAPI and Uvicorn: pip install fastapi uvicorn "pydantic[email]"
# 2. Run with Uvicorn: uvicorn digital_library.json_api:app --reload
#
# You can then access the API at http://127.0.0.1:8000
# And the interactive API docs (Swagger UI) at http://127.0.0.1:8000/docs