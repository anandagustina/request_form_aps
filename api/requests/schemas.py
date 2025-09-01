from pydantic import BaseModel
from typing import Optional

class RequestBase(BaseModel):
    judul: str
    deskripsi: str
    anggaran: int
    file_path: Optional[str] = None
    status: str
    created_date: str

class RequestCreate(RequestBase):
    pass

class RequestResponse(RequestBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True   # penting supaya bisa baca dari SQLAlchemy object
