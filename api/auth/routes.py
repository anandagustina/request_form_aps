from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.requests import Request
from config.database import get_db
from sqlalchemy.orm import Session
from api.auth.model import User
from api.auth.utils import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def do_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    templates = request.app.state.templates
    user = db.query(User).filter(User.username == username).first()

    if user and verify_password(password, user.password_hash):
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="uid", value=str(user.id), httponly=True)
        response.set_cookie(key="role", value=user.role, httponly=True)
        return response
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "msg": "Username atau password salah."}
        )


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="uid")
    response.delete_cookie(key="role")
    return response