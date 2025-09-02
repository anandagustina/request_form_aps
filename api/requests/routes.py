from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os

from config.database import get_db
from model import Request as RequestModel

router = APIRouter(prefix="/permintaan", tags=["permintaan"])

def require_login(request: Request) -> bool:
    return "uid" in request.cookies

def is_admin(request: Request) -> bool:
    return request.cookies.get("role") == "admin"


@router.post("/tambah")
async def add_request(
    request: Request,
    judul: str = Form(...),
    deskripsi: str = Form(...),
    anggaran: int = Form(...),
    file_upload: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not require_login(request):
        return RedirectResponse(url="/", status_code=303)

    UPLOAD_DIR = "uploaded_files"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = file_upload.filename or ""
    if not filename:
        return RedirectResponse(url="/dashboard", status_code=303)

    safe_name = filename.replace("/", "_").replace("\\", "_")
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file_upload.read())
    except Exception:
        return RedirectResponse(url="/dashboard", status_code=303)

    new_req = RequestModel(
        judul=judul,
        deskripsi=deskripsi,
        anggaran=anggaran,
        file_path=f"uploaded_files/{safe_name}",
        status="menunggu",
        created_date=datetime.now().isoformat(timespec="seconds"),
        user_id=int(request.cookies.get("uid")),
    )
    db.add(new_req)
    db.commit()

    return RedirectResponse(url="/dashboard", status_code=303)

@router.get("/setuju/{id}")
async def setuju_permintaaan(id: int, request: Request, db: Session = Depends(get_db)):
    permintaan = db.query(RequestModel).filter(RequestModel.id == id).first()

    if not permintaan:
        return RedirectResponse(url="/dashboard", status_code=303)

    permintaan.status = "disetujui"
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@router.get("/tolak/{id}")
async def tolak_permintaaan(id: int, request: Request, db: Session = Depends(get_db)):
    permintaan = db.query(RequestModel).filter(RequestModel.id == id).first()

    if not permintaan:
        return RedirectResponse(url="/dashboard", status_code=303)

    permintaan.status = "ditolak"
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@router.get("/hapus/{id}")
async def hapus_permintaan(id: int, request: Request, db: Session = Depends(get_db)):
    permintaan = db.query(RequestModel).filter(RequestModel.id == id).first()

    if not permintaan:
        return RedirectResponse(url="/dashboard", status_code=303)

    # cek apakah ada file yang tersimpan
    if permintaan.file_path:
        file_path = os.path.join("uploaded_files", os.path.basename(permintaan.file_path))
        if os.path.exists(file_path):
            os.remove(file_path)  # hapus file dari folder

    # hapus data dari DB
    db.delete(permintaan)
    db.commit()

    return RedirectResponse(url="/dashboard", status_code=303)
