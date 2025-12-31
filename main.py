import os

from dotenv import load_dotenv
from starlette.responses import RedirectResponse

from Core.security import Authentication

load_dotenv()
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware

from fastapi import  FastAPI,Request
from Controller.api import auth,books
from Controller import account,user,admin
from database import init_db,create_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    create_user()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
)
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/user/books")


app.include_router(account.router)
app.include_router(user.router)
app.include_router(admin.router)

app.include_router(auth.router)
app.include_router(books.router)