
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from config.database import SessionLocal, engine, Base
from api.auth.model import User
from api.auth.utils import verify_password
# ---------------------------------------------------------------------------- #
#                                  USER LOGIN                                  #
# ---------------------------------------------------------------------------- #


def login(db: Session = Depends(SessionLocal), username: str = "", password: str = ""):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return user