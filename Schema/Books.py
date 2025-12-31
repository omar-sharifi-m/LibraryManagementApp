from pydantic import BaseModel
from typing import List, Optional

class TagsSchema(BaseModel):
    id : int
    title : str

class TagSchema(BaseModel):
    title : str

class UserSchema(BaseModel):
    id: int
    username : str
class BookSchemaAll(BaseModel):
    id : int
    title : str
class BookSchema(BaseModel):
    id: int
    title: str
    author: str
    description: str
    front_cover: str

    pdf_url: Optional[str] = None
    audio_url: Optional[str] = None

    total_copies: int
    is_disable: bool
    creator_id: int

    tags: List[TagSchema]

    class Config:
        from_attributes = True
