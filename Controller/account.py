from fastapi import APIRouter, Depends, HTTPException,Request
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse,Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

import Form
from Core import Password
from Core.security import Authentication
from Form import SingupForm
from Model import User, UserRole
from database import get_db
from Core import flash_context

router = APIRouter(prefix="/account")

router.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals["flash_context"] = flash_context
@router.get("/login",response_class=HTMLResponse)
async def login_get(request: Request):
    form = Form.LoginForm()
    return templates.TemplateResponse("auth/login.j2",{"request":request,"form":form})


@router.post("/login",response_class=HTMLResponse)
async def login_post(request: Request,session:Session = Depends(get_db)):
    form = Form.LoginForm(await request.form())
    if not form.validate():
        return templates.TemplateResponse("auth/login.j2",{"request":request,"form":form})
    username = form.username.data
    password = form.password.data
    remember = form.remember.data
    model = session.query(User).where(User.username==username).first()
    if Password.verify(password,model.password):
        return Authentication.login({"user_id": model.id, "sub": model.username, "role": model.role},remember=remember,url = request.url_for("userIndex" if model.role == UserRole.USER else "adminIndex") )
    return templates.TemplateResponse("auth/login.j2",{"request":request,"form":form})

@router.get("/logout",response_class=HTMLResponse)
async def logout(request: Request):
    request.cookies.clear()
    response = RedirectResponse(url=request.url_for("login_get"),status_code=301)
    return response

@router.get("/register",response_class=HTMLResponse)
async def register(request: Request):
    form = SingupForm()
    return templates.TemplateResponse("auth/register.j2",{"request":request,"form":form})

@router.post("/register",response_class=HTMLResponse)
async def register(request: Request,session:Session = Depends(get_db)):
    form = SingupForm(await request.form())
    if form.validate():
        if form.password.data == form.password2.data:
            model = User(username=form.username.data,role=UserRole.USER,password=Password.hash(form.password.data))
            session.add(model)
            session.commit()
            return Authentication.login({"user_id": model.id, "sub": model.username, "role": model.role},remember=False,url = request.url_for("userIndex"))
    return RedirectResponse(url=request.url_for("register"),status_code=301)