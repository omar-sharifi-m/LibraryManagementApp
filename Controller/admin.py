from datetime import datetime, timedelta,UTC
from importlib.metadata import files
from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import select,func,and_
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
import uuid

from Core import Password, Files
from Core.security import Authentication

from Model import User, UserRole, Books, Tags, Loans
from Schema import TokenData
from database import get_db
from Core  import flash_context,remin_day

router = APIRouter(prefix="/admin", dependencies=[Depends(Authentication.adminLogin), Depends(Authentication.reqLogin)])
router.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals["flash_context"] = flash_context
templates.env.globals["remin_day"] = remin_day
@router.get("/", response_class=HTMLResponse)
async def adminIndex(request: Request,session: Session = Depends(get_db)):

    bookreq = session.query(Loans).where(Loans.is_loaned == False).limit(5)

    total_books = session.query(func.sum(Books.total_copies)).scalar() or 0
    available = session.query(Loans).where(and_(Loans.is_loaned == True,Loans.is_returnd == False)).count()
    deadlines = session.query(Loans).where(and_((Loans.deadline_date < datetime.now()),Loans.is_returnd == False)).count()
    return templates.TemplateResponse("admin/index.j2", {"request": request,"books" : bookreq, "total_books" : total_books, "available" : available,"deadlines":deadlines})


@router.post("/addbook")
async def adminAddBook(request: Request,
                       title: str= Form(...),
                       author: str =Form(...),
                       description: str = Form(...),
                       count: int = Form(...),
                       cover: UploadFile = File(...),
                       pdf: UploadFile = File(None),
                       audio: UploadFile = File(None),
                       tags_list: List[str] = Form([]),
                       session: Session = Depends(get_db),
                       user: TokenData = Depends(Authentication.reqLogin)):
    tags_obj = []
    for i in tags_list:
        tag = session.query(Tags).where(Tags.title == i).first()
        if not tag:
            tag = Tags(title=i)
            session.add(tag)
        session.flush()
        tags_obj.append(tag)
    model = Books(title=title,
                  author=author,
                  total_copies=count,
                  description=description,
                  creator_id=user.user_id,
                  tags = tags_obj
                  )
    file = Files()
    cover_name = file.safe_name(cover)
    file.upload(cover, cover_name)
    model.front_cover = cover_name
    if pdf.filename:
        pdf_name = file.safe_name(pdf)
        file.upload(pdf, pdf_name)
        model.pdf_url = pdf_name
    if audio.filename:
        audio_name = file.safe_name(audio)
        file.upload(audio, audio_name)
        model.audio_url = audio_name
    session.add(model)
    session.commit()
    url = request.headers.get("referer") or request.url_for("adminIndex")
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/books",response_class=HTMLResponse)
async def adminGetBooks(request: Request,session: Session = Depends(get_db),
                        page: int = Query(1, ge=1),
                        size: int = Query(4, ge=1, le=100),
                        q: str = Query(None),
                        tag_id: int = Query(None)):
    query = session.query(Books)
    if q:
        query = query.filter(
            (Books.title.icontains(q) | Books.description.icontains(q) | Books.author.icontains(q) )
        )
    skip = (page - 1) * size
    total_books = query.count()
    total_pages = (total_books + size - 1) // size
    books = query.order_by(Books.id.desc()).offset(skip).limit(size).all()
    file = Files()
    return templates.TemplateResponse("admin/books.j2", {
        "request": request,
        "books": books,
        "current_page": page,
        "total_pages": total_pages,
        "size": size,
        "url":file.url(),
        "q":q
    })
@router.get("/loans",response_class=HTMLResponse)
async def adminLoans(request: Request,session: Session = Depends(get_db)):
    loans = session.query(Loans).where(and_(Loans.is_loaned == False,Loans.is_rejected == False)).all()
    loansBookid =[]
    for i in loans:
        loansBookid.append(i.book_id)
    query = session.query(Loans).where(and_(Loans.is_loaned == True,Loans.is_returnd == False,Loans.book_id.in_(loansBookid))).all()
    book_count = {}
    for i in query:
        if book_count.get(i.book_id):
            book_count[i.book_id] += 1
        else:
            book_count[i.book_id] = 1
    res =[]
    for i in loans:
        temp = {
            "id": i.id,
            "book":i.book.title,
            "book_count":book_count.get(i.book_id,0),
            "total":i.book.total_copies,
            "user":i.user.username,
        }
        res.append(temp)
    return templates.TemplateResponse("admin/loans.j2",{"request":request,"loans":res})
@router.post("/loans/add",response_class=HTMLResponse)
async def add_loan_admin(request: Request,book:int = Form(...),user:int=Form(...),session: Session = Depends(get_db)):
    model = session.query(User).get(user)
    book_count = len(session.query(Loans).where(and_(Loans.is_loaned == True,Loans.is_returnd == False,Loans.book_id == book)).all())
    q = session.query(Books).get(book)

    if q.total_copies - book_count <= 0 :
        request.session["flush"] = "کتاب موجود نیست"
        return RedirectResponse(request.url_for("adminLoans"), status_code=status.HTTP_302_FOUND)
    if model:
        loan = Loans(book_id=book,
                     user_id=model.id,
                     loan_date=datetime.now(),
                     is_loaned=True,
                     deadline_date=datetime.now()+timedelta(days=14)
                     )
        session.add(loan)
        session.commit()
        request.session["flush"] = "ثبت شد"
        return RedirectResponse(request.url_for("adminLoans"), status_code=status.HTTP_302_FOUND)
    request.session["flush"] = "کاربر موجود نیست"
    return RedirectResponse(request.url_for("adminLoans"), status_code=status.HTTP_302_FOUND)

@router.get("/extension/{loan_id}")
async def add_loan_extension(loan_id:int,request: Request,session:Session = Depends(get_db)):
    model = session.get(Loans,loan_id)
    print(loan_id)
    print(model.deadline_date)
    if model:
        if model.deadline_date < datetime.now():
            model.deadline_date = datetime.now() + timedelta(days = 14)
        else:
            model.deadline_date = model.deadline_date + timedelta(days=14)
        session.add(model)
        session.commit()
        session.refresh(model)
        request.session["flush"] = "انجام شد"
        return RedirectResponse(request.url_for("admin_add_loans"), status_code=status.HTTP_302_FOUND)
    request.session["flush"] = "انجام نشد"
    return RedirectResponse(request.url_for("admin_add_loans"), status_code=status.HTTP_302_FOUND)
@router.get("/returns/{loan_id}")
async def adminReturns(loan_id:int,request: Request,session: Session = Depends(get_db)):
    model = session.query(Loans).get(loan_id)
    if model:
        model.is_returnd = True
        model.return_date = datetime.now()
        session.add(model)
        session.commit()
        request.session["flush"] = "انجام شد"
        return RedirectResponse(request.url_for("admin_add_loans"), status_code=status.HTTP_302_FOUND)
    request.session["flush"] = "انجام نشد"
    return RedirectResponse(request.url_for("admin_add_loans"), status_code=status.HTTP_302_FOUND)


@router.get("/loans_all",response_class=HTMLResponse)
async def admin_add_loans(request: Request,session: Session = Depends(get_db)):
    model =session.query(Loans).where(and_(Loans.is_returnd == False,Loans.is_rejected == False,Loans.is_loaned ==True)).all()
    return templates.TemplateResponse("admin/loan_all.j2",{"request":request,"loans":model})


@router.get("/reject/{loan_id}")
async def adminReject(loan_id:int,request: Request,session: Session = Depends(get_db)):
    model = session.query(Loans).get(loan_id)
    if model:
        model.is_rejected = True
        session.add(model)
        session.commit()
        request.session["flush"] = "انجام شد"
        return RedirectResponse(request.url_for("adminLoans"), status_code=status.HTTP_302_FOUND)
    request.session["flush"] = "انجام نشد"
    return RedirectResponse(request.url_for("adminLoans"), status_code=status.HTTP_302_FOUND)

@router.get("/accept/{loan_id}")
async def adminAccept(loan_id:int,request: Request,session: Session = Depends(get_db)):
    model = session.query(Loans).get(loan_id)
    if model:
        q = session.query(Loans).where(and_(Loans.is_loaned == True,Loans.is_returnd == False,Loans.book_id == model.book_id)).all()
        if model.book.total_copies - len(q) <= 0 :
            request.session["flush"] = "کتاب موجود نیست"
            return RedirectResponse(request.url_for("adminLoans"), status_code=status.HTTP_302_FOUND)
        model.is_loaned = True
        model.loan_date = datetime.now()
        model.deadline_date = datetime.now() + timedelta(days = 14)
        session.add(model)
        session.commit()
        request.session["flush"] = "انجام شد"
        return RedirectResponse(request.url_for("adminLoans"),status_code=status.HTTP_302_FOUND)
    request.session["flush"] = "انجام نشد"
    return RedirectResponse(request.url_for("adminLoans"),status_code=status.HTTP_302_FOUND)

@router.get("/book/edit/{book_id}")
async def edit_book(book_id:int,request: Request,session: Session = Depends(get_db)):
    book = session.get(Books,book_id)
    return templates.TemplateResponse("admin/book_edit.j2",{"request":request,"book":book})

@router.post("/book/edit/{book_id}")
async def edit_book_post(request: Request,
                         book_id:int,
                         title: str= Form(None),
                         author: str =Form(None),
                         description: str = Form(None),
                         count: int = Form(None),
                         cover: UploadFile = File(None),
                         pdf: UploadFile = File(None),
                         audio: UploadFile = File(None),
                         session: Session = Depends(get_db)):
    model = session.get(Books,book_id)
    if model is None:
        return RedirectResponse(request.url_for("getBook",book_id = book_id),status_code=status.HTTP_302_FOUND)
    if title:
        model.title = title
    if author:
        model.author = author
    if description:
        model.description = description
    if count:
        model.count = count
    f = Files()

    if cover.filename:
        print(f"Cover is Not None {cover.filename}")
        safe_name = f.safe_name(cover)
        f.upload(cover,safe_name)
        model.cover = safe_name

    if pdf.filename:
        safe_name = f.safe_name(pdf)
        f.upload(pdf,safe_name)
        model.pdf_url = safe_name
    if audio.filename:
        safe_name = f.safe_name(audio)
        f.upload(audio,safe_name)
        model.audio = safe_name
    session.add(model)
    session.commit()
    request.session["flush"] = "انجام شد"
    return RedirectResponse(request.url_for("getBook",book_id = book_id),status_code=status.HTTP_302_FOUND)