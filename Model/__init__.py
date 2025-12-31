from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Enum as SqlEnum, Table,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# ---------------- ENUM ----------------
class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    USER = "user"


# ---------------- USER ----------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    code_meli = Column(String, unique=True, nullable=True)
    firstName = Column(String)
    lastName = Column(String)
    password = Column(String, nullable=False)
    role = Column(
        SqlEnum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.USER
    )
    books = relationship("Books",back_populates="creator")
    loans = relationship("Loans", back_populates="user")
    scores = relationship("Score", back_populates="user")
    reviews = relationship("Review", back_populates="user")



class BookCondition(str, Enum):
    GOOD = "good"
    DAMAGED = "damaged"
    UNUSABLE = "unusable"


book_tags = Table(
    "book_tags",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)
class Books(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    description = Column(String, nullable=False)
    front_cover = Column(String, nullable=False)
    pdf_url = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    loans = relationship("Loans", back_populates="book")
    reviews = relationship("Review", back_populates="book")
    scores = relationship("Score", back_populates="book")
    total_copies = Column(Integer, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", back_populates="books")
    is_disable = Column(Boolean, nullable=True, default=False)
    tags = relationship(
        "Tags",
        secondary=book_tags,
        back_populates="books",
        passive_deletes=True,
    )



class Tags(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)

    # ✅ many-to-many
    books = relationship(
        "Books",
        secondary=book_tags,
        back_populates="tags"
    )



class Loans(Base):
    __tablename__ = "loans"
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reserve_date = Column(DateTime, nullable=True)
    loan_date = Column(DateTime, nullable=True)
    is_loaned = Column(Boolean, nullable=True, default=False)
    deadline_date = Column(DateTime, nullable=True)
    return_date = Column(DateTime, nullable=True)
    is_returnd = Column(Boolean, nullable=True, default=False)
    is_rejected = Column(Boolean, nullable=True, default=False)
    book = relationship("Books", back_populates="loans")
    user = relationship("User", back_populates="loans")


class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    value =  Column(Integer, nullable=True)
    book = relationship("Books", back_populates="scores")
    user = relationship("User", back_populates="scores")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    book = relationship("Books", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
