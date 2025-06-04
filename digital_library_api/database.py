# c:\src\digital-library\digital_library\database.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "sqlite:///./db.sqlite3"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # check_same_thread is needed for SQLite with Qt
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Book model
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    isbn = Column(String, unique=True, index=True)
    is_borrowed = Column(Boolean, default=False, nullable=False)
    borrower_name = Column(String, nullable=True)
    due_date = Column(Date, nullable=True)

    def __str__(self):
        status = ""
        if self.is_borrowed:
            status = f" (Borrowed by: {self.borrower_name or 'N/A'}, Due: {self.due_date or 'N/A'})"
        return f"{self.title} by {self.author} (ISBN: {self.isbn}){status}"

# Create database tables
def create_db_tables():
    Base.metadata.create_all(bind=engine)
