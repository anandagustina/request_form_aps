from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    judul = Column(String(255), nullable=False)
    deskripsi = Column(String(255), nullable=False)
    anggaran = Column(Integer, nullable=False)
    file_path = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="menunggu")
    created_date = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # --- Tambahan kolom untuk bukti transfer ---
    bukti_tf = Column(String(255), nullable=True)

    user = relationship("User", back_populates="requests")
