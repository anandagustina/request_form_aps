# seed.py
from config.database import SessionLocal, Base, engine
from api.auth.model import User
from api.requests.model import Request
from api.auth.utils import hash_password
from sqlalchemy.exc import IntegrityError
import datetime

# Buat semua tabel (jika belum ada)
Base.metadata.create_all(bind=engine)

# Buka session
session = SessionLocal()

try:
    # hapus semua data lama (jika ada)
    session.query(Request).delete()
    session.query(User).delete()
    session.commit()

    # --- Dummy Users ---
    user1 = User(username="admin", password_hash=hash_password("admin"), role="admin")
    user2 = User(username="user1", password_hash=hash_password("user1"), role="user")
    user3 = User(username="user2", password_hash=hash_password("user2"), role="user")

    session.add_all([user1, user2, user3])
    session.commit()

    # --- Dummy Requests ---
    req1 = Request(
        judul="Pengadaan Laptop",
        deskripsi="Permintaan laptop untuk tim IT",
        anggaran=15000000,
        file_path=None,
        status="menunggu",
        created_date=str(datetime.date.today()),
        user_id=user2.id
    )

    req2 = Request(
        judul="Renovasi Ruang Meeting",
        deskripsi="Perbaikan AC dan pencahayaan",
        anggaran=5000000,
        file_path=None,
        status="disetujui",
        created_date=str(datetime.date.today()),
        user_id=user3.id
    )

    session.add_all([req1, req2])
    session.commit()

    print("✅ Dummy data berhasil ditambahkan")

except IntegrityError:
    session.rollback()
    print("⚠️ Data sudah ada, tidak ditambahkan lagi")

finally:
    session.close()
