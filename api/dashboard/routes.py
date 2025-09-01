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
        permintaan = db.query(RequestModel).all()
        return templates.TemplateResponse("dashboard_admin.html", {"request": request, "permintaan": permintaan
        })
    
    else:
        return templates.TemplateResponse("dashboard_karyawan.html", {"request": request})
