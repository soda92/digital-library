# c:\src\digital-library\digital_library\json_api.py
import asyncio
import json
from datetime import date, timedelta, datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID

from fastapi import FastAPI, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

# --- Configuration ---
JSON_DB_FILE = "books_data.json"
DB_LOCK = asyncio.Lock()

# --- Pydantic Models ---
class BookBase(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    isbn: str = Field(..., min_length=10, max_length=13) # Basic ISBN length validation
    is_borrowed: bool = False
    borrower_name: Optional[str] = None
    due_date: Optional[date] = None

    @validator("due_date", "borrower_name", pre=True, always=True)
    def check_borrow_details(cls, v, values, field):
        is_borrowed = values.get("is_borrowed")
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
    title: Optional[str] = Field(None, min_length=1)
    author: Optional[str] = Field(None, min_length=1)
    isbn: Optional[str] = Field(None, min_length=10, max_length=13)
    # is_borrowed, borrower_name, due_date can be updated directly
    # but borrow/return endpoints are preferred for state changes.

class BookInDB(BookBase):
    id: UUID = Field(...)

# --- Database Helper Functions ---
async def load_db() -> Dict[str, Any]:
    async with DB_LOCK:
        try:
            with open(JSON_DB_FILE, "r") as f:
                try:
                    data = json.load(f)
                    # Ensure basic structure
                    if "books" not in data or "next_id" not in data: # next_id is legacy, using UUID now
                         data = {"books": {}, "next_id": 1} # books is now a dict keyed by UUID
                    # Convert date strings back to date objects if necessary
                    for book_id, book_data in data.get("books", {}).items():
                        if book_data.get("due_date") and isinstance(book_data["due_date"], str):
                            try:
                                book_data["due_date"] = datetime.strptime(book_data["due_date"], "%Y-%m-%d").date()
                            except ValueError:
                                book_data["due_date"] = None # or handle error
                    return data
                except json.JSONDecodeError:
                    return {"books": {}, "next_id": 1} # Initialize if file is empty/corrupt
        except FileNotFoundError:
            return {"books": {}, "next_id": 1} # Initialize if file doesn't exist

async def save_db(db_data: Dict[str, Any]):
    async with DB_LOCK:
        # Convert date objects to strings for JSON serialization
        books_to_save = {}
        for book_id, book_data_dict in db_data.get("books", {}).items():
            book_copy = book_data_dict.copy()
            if book_copy.get("due_date") and isinstance(book_copy["due_date"], date):
                book_copy["due_date"] = book_copy["due_date"].isoformat()
            books_to_save[book_id] = book_copy
        
        data_to_save = {"books": books_to_save, "next_id": db_data.get("next_id", 1)}

        with open(JSON_DB_FILE, "w") as f:
            json.dump(data_to_save, f, indent=4)

# --- FastAPI App ---
app = FastAPI(title="Digital Library JSON API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    # You can initialize the DB file here if it doesn't exist or needs setup
    db = await load_db()
    if not db.get("books"): # if books dict is empty
        await save_db({"books": {}, "next_id": 1})
    print(f"JSON Database API started. Using file: {JSON_DB_FILE}")

# --- API Endpoints ---

@app.post("/books/", response_model=BookInDB, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate):
    db = await load_db()
    # Check for ISBN uniqueness
    for existing_book_data in db["books"].values():
        if existing_book_data["isbn"] == book.isbn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Book with ISBN {book.isbn} already exists.",
            )

    book_id = uuid4()
    new_book_data = book.model_dump()
    new_book_data["id"] = book_id
    db["books"][str(book_id)] = new_book_data
    await save_db(db)
    return BookInDB(**new_book_data)

@app.get("/books/", response_model=List[BookInDB])
async def get_all_books():
    db = await load_db()
    return [BookInDB(**book_data) for book_data in db["books"].values()]

@app.get("/books/{book_id}", response_model=BookInDB)
async def get_book(book_id: UUID):
    db = await load_db()
    book_data = db["books"].get(str(book_id))
    if not book_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return BookInDB(**book_data)

@app.put("/books/{book_id}", response_model=BookInDB)
async def update_book(book_id: UUID, book_update: BookUpdate):
    db = await load_db()
    book_data_dict = db["books"].get(str(book_id))
    if not book_data_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Check for ISBN uniqueness if ISBN is being changed
    if book_update.isbn and book_update.isbn != book_data_dict["isbn"]:
        for b_id, b_data in db["books"].items():
            if b_id != str(book_id) and b_data["isbn"] == book_update.isbn:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Another book with ISBN {book_update.isbn} already exists.",
                )
    
    update_data = book_update.model_dump(exclude_unset=True)
    
    # Validate borrow details if is_borrowed is changing or relevant fields are updated
    # Pydantic model validation should handle this on BookUpdate instantiation if data is passed correctly
    # However, we need to ensure consistency if is_borrowed is flipped.
    if 'is_borrowed' in update_data:
        if update_data['is_borrowed']:
            if not update_data.get('borrower_name') or not update_data.get('due_date'):
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="If setting is_borrowed to true, borrower_name and due_date are required."
                )
        else: # if setting is_borrowed to false
            update_data['borrower_name'] = None
            update_data['due_date'] = None

    updated_book_data = {**book_data_dict, **update_data}
    
    # Re-validate with BookBase to ensure consistency after merge
    try:
        BookBase(**updated_book_data) 
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db["books"][str(book_id)] = updated_book_data
    await save_db(db)
    return BookInDB(**updated_book_data)


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: UUID):
    db = await load_db()
    if str(book_id) not in db["books"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    del db["books"][str(book_id)]
    await save_db(db)
    return None

@app.post("/books/{book_id}/borrow", response_model=BookInDB)
async def borrow_book_action(
    book_id: UUID, 
    borrower_name: str = Body(..., embed=True, min_length=1),
    borrow_days: int = Body(14, embed=True, gt=0)
):
    db = await load_db()
    book_data = db["books"].get(str(book_id))
    if not book_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if book_data["is_borrowed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book is already borrowed by {book_data['borrower_name']}",
        )

    book_data["is_borrowed"] = True
    book_data["borrower_name"] = borrower_name
    book_data["due_date"] = date.today() + timedelta(days=borrow_days)
    
    db["books"][str(book_id)] = book_data # Update the entry in the db dict
    await save_db(db)
    return BookInDB(**book_data)

@app.post("/books/{book_id}/return", response_model=BookInDB)
async def return_book_action(book_id: UUID):
    db = await load_db()
    book_data = db["books"].get(str(book_id))
    if not book_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if not book_data["is_borrowed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Book is not currently borrowed"
        )

    book_data["is_borrowed"] = False
    book_data["borrower_name"] = None
    book_data["due_date"] = None
    
    db["books"][str(book_id)] = book_data # Update the entry in the db dict
    await save_db(db)
    return BookInDB(**book_data)

# To run this API (save as json_api.py):
# 1. Install FastAPI and Uvicorn: pip install fastapi uvicorn "pydantic[email]"
# 2. Run with Uvicorn: uvicorn digital_library.json_api:app --reload
#
# You can then access the API at http://127.0.0.1:8000
# And the interactive API docs (Swagger UI) at http://127.0.0.1:8000/docs