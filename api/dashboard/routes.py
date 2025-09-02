from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from config.database import get_db
from sqlalchemy.orm import Session
from api.auth.model import User as UserModel
from api.requests.model import Request as RequestModel


router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    templates = request.app.state.templates

    role = request.cookies.get("role")
    if not role:
        return RedirectResponse(url="/auth/login", status_code=303)

    if role == "admin":
        permintaan = db.query(RequestModel, UserModel.username).join(UserModel, RequestModel.user_id == UserModel.id).all()
        admin_id = int(request.cookies.get("uid"))
        admin_user = db.query(UserModel).filter(UserModel.id == admin_id).first()
        permintaan_data = [
        {
            "id": r.Request.id,
            "judul": r.Request.judul,
            "deskripsi": r.Request.deskripsi,
            "anggaran": r.Request.anggaran,
            "file_path": r.Request.file_path,
            "status": r.Request.status,
            "created_at": r.Request.created_date,
            "username": r.username,  # ini dari tabel User
        }
        for r in permintaan
    ]
        return templates.TemplateResponse(
        "dashboard_admin.html",
        {
            "request": request,
            "username": admin_user.username,
            "permintaan": permintaan_data
        }
    )
    
    else:
        return templates.TemplateResponse("dashboard_karyawan.html", {"request": request})
