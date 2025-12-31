from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from Model import Base, User,UserRole
from Core import Password

from os import getenv,environ


SQLALCHEMY_DATABASE_URL = getenv("DATABASE_URL")
# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)

def create_user():
    session = SessionLocal()
    if not session.query(User).where(User.username =="admin@gmail.com").first():
        model = User(
            username="admin@gmail.com",
            password=Password.hash("admin1234"),
            role=UserRole.ADMIN,
        )
        session.add(model)
        session.commit()

if __name__ == "__main__":
    init_db()
    create_user()
    print("Database initialized successfully!")
