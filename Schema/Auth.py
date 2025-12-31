from pydantic import BaseModel
from typing import Optional



class Login(BaseModel):
    username: str
    password: str

class Singup(BaseModel):
    username: str
    password: str