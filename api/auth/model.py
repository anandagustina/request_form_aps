from config.database import SessionLocal
from api.auth.utils import hash_password
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)

    requests = relationship("Request", back_populates="user")