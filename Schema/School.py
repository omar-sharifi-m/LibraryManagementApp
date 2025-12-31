from pydantic import BaseModel
from typing import List
class Create(BaseModel):
    name: str

class SchoolInfo(BaseModel):
    id: int
    name: str
    owner: bool

class UserWithSchools(BaseModel):
    id: int
    username: str
    schools: List[SchoolInfo]
