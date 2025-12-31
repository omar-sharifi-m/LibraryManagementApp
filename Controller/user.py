from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Query,Form
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import RedirectResponse


from Core import Files, Password
from Core.security import Authentication

from Model import Books, Tags, Score, Loans,User
from Schema import TokenData
from database import get_db
from Core import flash_context,remin_day

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
templates.env.globals["remain_day"] = remin_day

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

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, session: Session = Depends(get_db),user:TokenData = Depends(Authentication.reqLogin)):
    profile = session.get(User,user.user_id)
    return templates.TemplateResponse("dashboard/profile.j2",{"request": request,"profile": profile})
@router.post("/profile/update")
async def update_profile(request: Request, session: Session = Depends(get_db),user:TokenData = Depends(Authentication.reqLogin)
                         ,code_meli:str=Form(None),
                         last_name:str=Form(None),
                         first_name:str=Form(None),
password:str=Form(None),
                         ):
    model = session.get(User,user.user_id)
    if code_meli:
        model.code_meli = code_meli
    if last_name:
        model.lastName = last_name
    if first_name:
        model.firstName = first_name
    if password:
        model.password = Password.hash(password)
    session.commit()
    return RedirectResponse(request.url_for("profile"),status_code=status.HTTP_302_FOUND)
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
    query = session.query(Loans).where(Loans.user_id == user.user_id)
    total_loans = len(query.where(and_(Loans.is_loaned == True)).all())
    in_loan_book = query.where(and_(Loans.is_loaned == True,Loans.is_returnd == False)).all()
    f = Files()

    return templates.TemplateResponse("dashboard/index.j2",{"request": request,"total_loans":total_loans, "in_loan_book":in_loan_book,"in_loan_len":len(in_loan_book),"url": f.url()})


@router.get("/dashboard/Books", response_class=HTMLResponse)
async def dashboardBooks(request: Request, session: Session = Depends(get_db), user: TokenData = Depends(Authentication.reqLogin)):
    query = session.query(Loans).where(Loans.user_id == user.user_id)
    total_loans = len(query.where(and_(Loans.is_loaned == True)).all())
    in_loan_book = query.where(and_(Loans.is_loaned == True,Loans.is_returnd == False)).all()
    all_book = query.where(and_(Loans.is_loaned == True,Loans.is_returnd == True)).all()
    f = Files()

    return templates.TemplateResponse("dashboard/books.j2",{"request": request,"all_book":all_book,"allBookLen":len(all_book),"total_loans":total_loans,"in_loan_len":len(in_loan_book),"url": f.url()})


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
