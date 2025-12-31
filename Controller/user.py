from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import RedirectResponse


from Core import Files
from Core.security import Authentication

from Model import Books, Tags, Score, Loans
from Schema import TokenData
from database import get_db
from Core import flash_context

router = APIRouter(prefix="/user")

router.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def inject_user(request: Request):
    token = request.cookies.get("access_token")
    user = Authentication.validateToken(token) if token else None
    return {
        "current_user": user,
        "is_authenticated": user is not None
    }

def average_score(scores:List[Score]):
    res = 0
    if len(scores) == 0:
        return 0
    for score in scores:
        res += score.value
    return res // len(scores)

templates.env.globals["inject_user"] = inject_user
templates.env.globals["average_score"] = average_score
templates.env.globals["flash_context"] = flash_context

@router.get("/books", response_class=HTMLResponse)
async def userIndex(request: Request, session: Session = Depends(get_db), q: str = Query(None),
                    tag_id: int = Query(-1)):
    query = session.query(Books).order_by(Books.id.desc())
    if q:
        query = query.filter(
            (Books.title.icontains(q) | Books.description.icontains(q) | Books.author.icontains(q))
        )
    if tag_id >= 0:
        query = query.filter(Books.tags.any(Tags.id == tag_id))
    books = query.limit(4).all()
    tags = session.query(Tags)
    file = Files()
    return templates.TemplateResponse("user/books.j2",
                                      {"request": request, "books": books, "url": file.url(), "tags": tags.all(),
                                       "tag": tags.where(Tags.id == tag_id).first().title if tag_id >= 0 else None})


@router.get("/books/{book_id}",response_class=HTMLResponse)
async def getBook(book_id: int, request: Request, session: Session = Depends(get_db)):
    book = session.query(Books).options(selectinload(Books.tags),
                                                                         selectinload(Books.reviews),
                                                                         selectinload(Books.loans),
                                                                         selectinload(Books.scores),
                                                                         ).get(book_id)
    file = Files()
    return templates.TemplateResponse("user/book.j2", {"request": request, "url": file.url(), "book": book})

@router.get("/books/{book_id}/score/{score}")
async def setScore(request:Request,book_id:int,score:int,session: Session = Depends(get_db),user:TokenData = Depends(Authentication.reqLogin)):
    model = session.query(Score).filter(
        and_(
            Score.book_id == book_id,
            Score.user_id == user.user_id
        )
    ).first()
    if model:
        model.value = score
    else:
        session.add(Score(
            book_id=book_id,
            user_id=user.user_id,
            value=score
        ))
    session.commit()
    return RedirectResponse(request.url_for("getBook", book_id=book_id),status_code=status.HTTP_302_FOUND)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, session: Session = Depends(get_db),
                    user: TokenData = Depends(Authentication.reqLogin)):
    return templates.TemplateResponse("user/dashboard.j2",{"request": request})

@router.get("/books/{book_id}/reserve", response_class=HTMLResponse)
async def reserve(request:Request,book_id:int,session: Session = Depends(get_db), user: TokenData = Depends(Authentication.reqLogin)):
    model =  session.query(Loans).where(and_(Loans.book_id == book_id, Loans.user_id == user.user_id,Loans.is_returnd == False)).first()
    if model:
        if model.is_rejected:
            request.session["flush"] = "درخواست شما رد شده است "
            return RedirectResponse(request.url_for("getBook", book_id=book_id),status_code=status.HTTP_302_FOUND)
        request.session["flush"] = "در حال بررسی است "
        return RedirectResponse(request.url_for("getBook", book_id=book_id),status_code=status.HTTP_302_FOUND)
    model = Loans(
        book_id=book_id,
        user_id=user.user_id,
        is_returnd=False,
        is_loaned=False,
        is_rejected=False,
        reserve_date=datetime.now())
    session.add(model)
    session.commit()
    request.session["flush"] = "درخواست ثبت شد"
    return RedirectResponse(request.url_for("getBook", book_id=book_id), status_code=status.HTTP_302_FOUND)
