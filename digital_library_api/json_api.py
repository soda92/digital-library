from datetime import date, timedelta, datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from .database import SessionLocal, Book as DBBook, User as DBUser, create_db_tables
from .models import (
    Token,
    TokenData,
    User,
    UserCreate,
    BookBase,
    BookCreate,
    BookUpdate,
    BookInDB,
)
import os


# --- Authentication Configuration ---
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "YOUR_VERY_SECRET_KEY_CHANGE_THIS"
)  # IMPORTANT: Change this and keep it secret!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Utility Functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> DBUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = db.query(DBUser).filter(DBUser.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    On startup, it ensures database tables are created.
    """
    # Ensure database tables are created
    create_db_tables()
    print(f"SQLite Database API started. Using database: {SessionLocal().bind.url}")
    yield
    # Add any shutdown logic here if needed in the future
    print("SQLite Database API shutting down.")


# --- API Endpoints ---
app.router.lifespan_context = lifespan


# --- User and Authentication Endpoints ---
@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = DBUser(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(DBUser).filter(DBUser.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/books/", response_model=BookInDB, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):  # Added current_user for consistency if needed later
    existing_book = db.query(DBBook).filter(DBBook.isbn == book.isbn).first()
    if existing_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book with ISBN {book.isbn} already exists.",
        )

    # Ensure borrower_name is not part of book.model_dump() if BookCreate still had it
    book_data = book.model_dump(exclude_unset=True)
    if "borrower_name" in book_data:  # Should not happen if model is updated
        del book_data["borrower_name"]

    db_book = DBBook(**book_data)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return BookInDB.model_validate(db_book)


@app.get("/books/", response_model=List[BookInDB])
async def get_all_books(db: Session = Depends(get_db)):
    books = db.query(DBBook).all()
    # Populate borrower_username
    result = []
    for book in books:
        book_data = BookInDB.model_validate(book).model_dump()
        if book.borrower:
            book_data["borrower_username"] = book.borrower.username
        result.append(BookInDB(**book_data))
    return result


@app.get("/books/{book_id}", response_model=BookInDB)  # book_id is now int
async def get_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    book_data = BookInDB.model_validate(db_book).model_dump()
    if db_book.borrower:
        book_data["borrower_username"] = db_book.borrower.username
    return BookInDB(**book_data)


@app.put("/books/{book_id}", response_model=BookInDB)  # book_id is now int
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user), # <--- ADD THIS
):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )

    update_data = book_update.model_dump(exclude_unset=True)

    # Check for ISBN uniqueness if ISBN is being changed
    if "isbn" in update_data and update_data["isbn"] != db_book.isbn:
        existing_book = (
            db.query(DBBook)
            .filter(DBBook.isbn == update_data["isbn"], DBBook.id != book_id)
            .first()
        )
        if existing_book:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another book with ISBN {update_data['isbn']} already exists.",
            )

    # Handle is_borrowed changes carefully
    if "is_borrowed" in update_data and update_data["is_borrowed"] is False:
        # This is effectively a "return" action if the book was borrowed.
        db_book.is_borrowed = False
        db_book.borrower_id = None
        db_book.due_date = None
        # Remove is_borrowed from update_data so it's not re-applied by the loop
        del update_data["is_borrowed"]
        if "due_date" in update_data:  # due_date should be cleared
            del update_data["due_date"]

    elif "is_borrowed" in update_data and update_data["is_borrowed"] is True:
        # Disallow borrowing via PUT if the book is not already borrowed by someone else
        # Or if trying to change borrower. Use /borrow endpoint for that.
        if not db_book.is_borrowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot borrow book using PUT. Use the /borrow endpoint.",
            )
        # If already borrowed, and is_borrowed:true is passed, it's a no-op for borrowing status.
        # We might still want to update due_date if provided.
        # For simplicity, we'll let due_date be updated if provided, but is_borrowed status itself is tricky here.
        # Let's assume if is_borrowed:true is passed and it's already borrowed, we only update other fields.
        pass  # is_borrowed state remains true, other fields might be updated.

    # Apply other updates
    for key, value in update_data.items():
        if hasattr(db_book, key):
            setattr(db_book, key, value)

    # Validate the final state of the book model before commit (optional, depends on how strict)
    try:
        BookBase.model_validate(db_book)  # Validate against base rules
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db.commit()
    db.refresh(db_book)
    return db_book


@app.delete(
    "/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT
)  # book_id is now int
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )

    db.delete(db_book)
    db.commit()
    return None


@app.post("/books/{book_id}/borrow", response_model=BookInDB)  # book_id is now int
async def borrow_book_action(
    book_id: int,
    # borrower_name: str = Body(..., embed=True, min_length=1), # Removed
    borrow_days: int = Body(14, embed=True, gt=0),
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),  # Added
):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    if db_book.is_borrowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book is already borrowed by {db_book.borrower.username if db_book.borrower else 'another user'}",
        )

    db_book.is_borrowed = True
    db_book.borrower_id = current_user.id  # Use authenticated user's ID
    db_book.due_date = date.today() + timedelta(days=borrow_days)

    db.commit()
    db.refresh(db_book)
    book_data = BookInDB.model_validate(db_book).model_dump()
    book_data["borrower_username"] = current_user.username
    return BookInDB(**book_data)


@app.post("/books/{book_id}/return", response_model=BookInDB)  # book_id is now int
async def return_book_action(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    db_book = db.query(DBBook).filter(DBBook.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    if not db_book.is_borrowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book is not currently borrowed",
        )
    # Optional: Check if the current_user is the one who borrowed it, if strict return policy is needed
    # if db_book.borrower_id != current_user.id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You did not borrow this book.")

    db_book.is_borrowed = False
    db_book.borrower_id = None  # Clear borrower ID
    db_book.due_date = None

    db.commit()
    db.refresh(db_book)
    return db_book


# To run this API:
# 1. Install FastAPI and Uvicorn: pip install fastapi uvicorn "pydantic[email]"
# 2. Run with Uvicorn: uvicorn digital_library.json_api:app --reload
#
# You can then access the API at http://127.0.0.1:8000
# And the interactive API docs (Swagger UI) at http://127.0.0.1:8000/docs
