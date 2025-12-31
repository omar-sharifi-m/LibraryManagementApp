from fastapi import APIRouter, Depends, HTTPException,Request
from sqlalchemy.orm import Session
from Core import (AccessToken,
                  Password)

from Schema import (Login as LoginSchema,
                    Token as TokenSchema,
                    Singup as SingupSchema,
                    )

from database import get_db
from Model import User

router = APIRouter(prefix="/api/auth", tags=["auth"],dependencies=[])


@router.post("/login",response_model=TokenSchema)
async def login(user: LoginSchema, session: Session = Depends(get_db)):
    model = session.query(User).where(User.username == user.username).first()
    if model and Password.verify(user.password,str(model.password)):
        data = AccessToken.create({"user_id": model.id, "sub": model.username, "role": model.role})
        return {"access_token": data,"token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Incorrect password or username")

@router.post("/singup",response_model=TokenSchema)
async def singup(user:SingupSchema ,session: Session = Depends(get_db)):
    if session.query(User).where(User.username == user.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    model = User(username=user.username, password=Password.hash(user.password))
    session.add(model)
    session.commit()
    data = AccessToken.create({"user_id": model.id, "sub": model.username, "role": model.role})
    return {"access_token": data,"token_type": "bearer"}