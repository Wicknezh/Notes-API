from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import Role
from typing import Literal

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=72)
    role: Literal["admin", "user", "viewer"] = "viewer"


class UserOut(BaseModel):
    id: int
    username: str
    role: Role

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"




class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None


class NoteOut(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)