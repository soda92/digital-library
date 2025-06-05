from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm import declarative_base

DATABASE_URL = "sqlite:///./db.sqlite3"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # check_same_thread is needed for SQLite with Qt
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    borrowed_books = relationship("Book", back_populates="borrower")

# Define the Book model
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, index=True, nullable=False)
    isbn = Column(String, unique=True, index=True, nullable=False)
    is_borrowed = Column(Boolean, default=False, nullable=False)
    due_date = Column(Date, nullable=True)

    borrower_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    borrower = relationship("User", back_populates="borrowed_books")

    def __str__(self):
        status = ""
        if self.is_borrowed and self.borrower:
            status = f" (Borrowed by: {self.borrower.username}, Due: {self.due_date or 'N/A'})"
        elif self.is_borrowed: # Fallback if borrower object isn't loaded or ID is all we have
            status = f" (Borrowed by User ID: {self.borrower_id}, Due: {self.due_date or 'N/A'})"
        return f"{self.title} by {self.author} (ISBN: {self.isbn}){status}"

# Create database tables
def create_db_tables(engine=engine):
    Base.metadata.create_all(bind=engine)
