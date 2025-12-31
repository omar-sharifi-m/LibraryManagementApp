from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session, selectinload
from Core import (AccessToken,
                  Password)

from Schema import (TagSchema)
from typing import List

from Schema.Books import BookSchema, BookSchemaAll, UserSchema
from database import get_db
from Model import User, Books, Tags

router = APIRouter(prefix="/api/books", tags=["books"], dependencies=[])


@router.get("/tags",response_model=List[TagSchema])
def get_tags(session: Session = Depends(get_db)):
    return [{"title": i.title} for i in session.query(Tags).all()]


@router.get("/books",response_model=List[BookSchema])
def get_books(session: Session = Depends(get_db),
              c: int = Query(0),
              q: str = Query(None),
              tag_id: int = Query(-1)):
    query = session.query(Books).order_by(Books.id.desc())
    if q:
        query = query.filter(
            (Books.title.icontains(q) | Books.description.icontains(q) | Books.author.icontains(q))
        )
    if tag_id >= 0:
        query = query.filter(Books.tags.any(Tags.id == tag_id))
    books = query.options(selectinload(Books.tags)).offset(c).limit(4).all()
    return books

@router.get("/allBook",response_model=List[BookSchemaAll],dependencies=[Depends(AccessToken.verify),Depends(AccessToken.admin)])
async def get_all_books(session: Session = Depends(get_db)):
    return session.query(Books.id,Books.title).all()

@router.get("/users",response_model=List[UserSchema],dependencies=[Depends(AccessToken.verify),Depends(AccessToken.admin)])
async def get_all_users(session: Session = Depends(get_db)):
    return session.query(User.id,User.username).all()