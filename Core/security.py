from datetime import datetime, timedelta, timezone
from typing import Optional
from starlette.responses import RedirectResponse, Response,URL
from fastapi import (Request,
                    Depends,
                    HTTPException,
                    status)
from fastapi.security import (HTTPBearer,
                              HTTPAuthorizationCredentials
)
from jose import (jwt,
                  JWTError,
                  ExpiredSignatureError
)
from passlib.hash import pbkdf2_sha256

from Model import UserRole
from Schema import TokenData
import os
import dotenv


class Password:
    def hash(secret:str)->str:
        return pbkdf2_sha256.hash(secret)
    def verify(secret:str, hash:str)->bool:
        return pbkdf2_sha256.verify(secret, hash)

dotenv.load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

security_scheme = HTTPBearer()


class Authentication:
    def login(data:dict,remember:bool=False,url = "/user" )->Response:
        resp = RedirectResponse(url=url,status_code=status.HTTP_302_FOUND)
        expires = (60*30*24) if remember else ACCESS_TOKEN_EXPIRE_MINUTES
        resp.set_cookie(
            key="access_token",
            value =f"{AccessToken.create(data= data,expire_date=expires)}",
            httponly=True,
            samesite="lax",
            max_age=expires if remember else None,
        )
        return resp
    def reqLogin(request: Request)-> TokenData | HTTPException:
        token = request.cookies.get("access_token")
        if token :
            data =Authentication.validateToken(token)
            return TokenData(user_id=data.get("user_id"),role=data.get("role"),username=data.get("sub"))
        request.session["flush"] = "لطفا وارد حساب خود شوید"
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT,headers={"Location": "/account/login"})
    def adminLogin(request: Request)-> TokenData|HTTPException:
        token =Authentication.validateToken(request.cookies.get("access_token"))
        if token :
            user = UserRole(token.get("role"))
            if  user== UserRole.ADMIN:
                return TokenData(user_id=token.get("user_id"),role=token.get("role"),username=token.get("sub"))
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT,headers={"Location": "/account/login"})
    def validateToken(token:str)->Optional[dict]|Response:
        try:
            return jwt.decode(token,SECRET_KEY,ALGORITHM)
        except JWTError:
            return None
        except:
            return None


class AccessToken:
    def create(data:dict,expire_date:int =ACCESS_TOKEN_EXPIRE_MINUTES )->str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_date)
        data.update({"exp":expire})
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    def verify(credentials: HTTPAuthorizationCredentials = Depends(security_scheme))->TokenData:
        token = credentials.credentials
        payload = AccessToken.validateToken(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized",headers={"WWW-Authenticate":"Bearer"})
        username = payload.get("sub")
        id = payload.get("user_id")
        role = payload.get("role")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized",headers={"WWW-Authenticate":"Bearer"})
        return TokenData(username = username,user_id=id, role=role)


    def admin(user:TokenData= Depends(verify))->TokenData:
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    def staff(user:TokenData= Depends(verify))->TokenData:
        if user.role != UserRole.STAFF:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff role required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    def validateToken(data:str)->Optional[dict]:
        try:
            return jwt.decode(data, SECRET_KEY, algorithms=[ALGORITHM])
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

