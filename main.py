import os
import sqlite3
import hashlib
from datetime import datetime
import uvicorn
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "app.db")

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))

# Serve uploaded files
UPLOAD_DIR = os.path.join(APP_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploaded_files", StaticFiles(directory=UPLOAD_DIR), name="uploaded_files")

# ---------- DB UTILS ----------
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','karyawan'))
        )
    """)
    # requests
    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            judul TEXT NOT NULL,
            deskripsi TEXT NOT NULL,
            anggaran REAL,
            file_path TEXT,
            status TEXT NOT NULL CHECK(status IN ('Menunggu','Disetujui','Ditolak')) DEFAULT 'Menunggu',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # insert some initial data
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", hash_password("admin123"), "admin"))
        cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("budi", hash_password("budi123"), "karyawan"))
        cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("siti", hash_password("siti123"), "karyawan"))
        conn.commit()

# ---------- AUTH UTILS ----------
def get_user_by_id(user_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cur.fetchone()

def require_login(request: Request) -> bool:
    return "uid" in request.cookies

def is_admin(request: Request) -> bool:
    return request.cookies.get("role") == "admin"

# ---------- CORE ROUTES ----------
@app.get("/", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def do_login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    
    if user and user["password_hash"] == hash_password(password):
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="uid", value=str(user["id"]), httponly=True)
        response.set_cookie(key="role", value=user["role"], httponly=True)
        return response
    else:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "msg": "Username atau password salah."}
        )

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="uid")
    response.delete_cookie(key="role")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if not require_login(request):
        return RedirectResponse(url="/", status_code=303)

    user_role = request.cookies.get("role")
    user_id = int(request.cookies.get("uid"))
    
    conn = get_db()
    cur = conn.cursor()

    if user_role == "admin":
        cur.execute("SELECT T1.*, T2.username FROM requests AS T1 JOIN users AS T2 ON T1.user_id = T2.id ORDER BY T1.created_at DESC")
        permintaan = cur.fetchall()
        
        user = get_user_by_id(user_id)
        return templates.TemplateResponse(
            "dashboard_admin.html", 
            {"request": request, "username": user["username"], "permintaan": permintaan}
        )
    else: # Karyawan
        cur.execute("SELECT * FROM requests WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        permintaan = cur.fetchall()
        
        user = get_user_by_id(user_id)
        return templates.TemplateResponse(
            "dashboard_karyawan.html", 
            {"request": request, "username": user["username"], "permintaan": permintaan}
        )

# ---------- USERS MANAGEMENT (ADMIN ONLY) ----------
@app.get("/users")
def users_list(request: Request, msg: str = None, err: str = None):
    if not require_login(request) or not is_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY role DESC, username ASC")
    users = cur.fetchall()
    return templates.TemplateResponse("users.html", {"request": request, "users": users, "msg": msg, "err": err})

@app.get("/users/tambah")
def users_tambah(request: Request, err: str = None):
    if not require_login(request) or not is_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(
        "users_form.html", 
        {"request": request, "title": "Tambah User", "action": "/users/tambah", "user": {"username":"", "role": "karyawan"}, "is_edit": False, "err": err}
    )

@app.post("/users/tambah")
async def users_do_tambah(request: Request, username: str = Form(...), password: str = Form(...), role: str = Form(...)):
    if not require_login(request) or not is_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, hash_password(password), role))
        conn.commit()
    except sqlite3.IntegrityError:
        return templates.TemplateResponse(
            "users_form.html",
            {
                "request": request, 
                "title": "Tambah User",
                "action": "/users/tambah",
                "user": {"username": username, "role": role},
                "is_edit": False,
                "err": "Username sudah dipakai."
            }
        )
    
    return RedirectResponse(url="/users?msg=User+berhasil+ditambahkan", status_code=303)

@app.get("/users/edit/{uid}")
def users_edit(uid: int, request: Request, err: str = None):
    if not require_login(request) or not is_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    
    user = get_user_by_id(uid)
    if not user:
        return RedirectResponse(url="/users?err=User+tidak+ditemukan", status_code=303)
        
    return templates.TemplateResponse(
        "users_form.html", 
        {"request": request, "title": "Edit User", "action": f"/users/edit/{uid}", "user": user, "is_edit": True, "err": err}
    )

@app.post("/users/edit/{uid}")
async def users_do_edit(uid: int, request: Request, username: str = Form(...), password: str = Form(""), role: str = Form(...)):
    if not require_login(request) or not is_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)
        
    conn = get_db()
    cur = conn.cursor()
    
    try:
        if password: # ganti password
            cur.execute("UPDATE users SET username=?, password_hash=?, role=? WHERE id=?", (username, hash_password(password), role, uid))
        else: # jangan ganti password
            cur.execute("UPDATE users SET username=?, role=? WHERE id=?", (username, role, uid))
        conn.commit()
    except sqlite3.IntegrityError:
        user = get_user_by_id(uid)
        return templates.TemplateResponse(
            "users_form.html",
            {
                "request": request, 
                "title": "Edit User",
                "action": f"/users/edit/{uid}",
                "user": user,
                "is_edit": True,
                "err": "Username sudah dipakai."
            }
        )
    
    return RedirectResponse(url=f"/users?msg=User+{username}+berhasil+diperbarui", status_code=303)

def count_admins_excluding(uid: int) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND id != ?", (uid,))
    return cur.fetchone()[0]

@app.get("/users/hapus/{uid}")
def users_delete(uid: int, request: Request):
    if not require_login(request) or not is_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    my_uid = int(request.cookies.get("uid"))

    if uid == my_uid:
        return RedirectResponse(url="/users?err=Tidak+bisa+hapus+akun+sendiri", status_code=303)

    target = get_user_by_id(uid)
    if not target:
        return RedirectResponse(url="/users?err=User+tidak+ditemukan", status_code=303)

    if target["role"] == "admin" and count_admins_excluding(uid) == 0:
        return RedirectResponse(url="/users?err=Tetap+butuh+minimal+1+admin", status_code=303)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    return RedirectResponse(url="/users?msg=User+berhasil+dihapus", status_code=303)

# ---------- REQUESTS (KARYAWAN) ----------
@app.post("/permintaan/tambah")
async def add_request(
    request: Request,
    judul: str = Form(...),
    deskripsi: str = Form(...),
    anggaran: float = Form(...),
    file_pdf: UploadFile = File(...)
):
    if not require_login(request):
        return RedirectResponse(url="/", status_code=303)
    
    user_id = int(request.cookies.get("uid"))

    # Validate extension is PDF
    filename = file_pdf.filename or ""
    if not filename.lower().endswith(".pdf"):
        return templates.TemplateResponse(
            "dashboard_karyawan.html",
            {"request": request, "username": get_user_by_id(user_id)["username"], "permintaan": [], "err": "File harus berformat PDF."}
        )
    
    # Save file
    safe_name = filename.replace("/", "_").replace("\\", "_")
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as buffer:
        buffer.write(await file_pdf.read())

    # Store DB path relative to mount
    rel_path = f"uploaded_files/{safe_name}"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO requests (user_id, judul, deskripsi, anggaran, file_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, judul, deskripsi, anggaran, rel_path, datetime.now().isoformat(timespec="seconds"))
    )
    conn.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

# ---------- REQUESTS (ADMIN) ----------
@app.get("/permintaan/setuju/{req_id}")
def approve_request(req_id: int, request: Request):
    if not require_login(request) or not is_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE requests SET status = 'Disetujui' WHERE id = ?", (req_id,))
    conn.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/permintaan/tolak/{req_id}")
def reject_request(req_id: int, request: Request):
    if not require_login(request) or not is_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE requests SET status = 'Ditolak' WHERE id = ?", (req_id,))
    conn.commit()
    return RedirectResponse(url="/dashboard", status_code=303)
    
# ---------- OPTIONAL: hapus permintaan (admin) ----------
@app.get("/permintaan/hapus/{req_id}")
def permintaan_hapus(req_id: int, request: Request):
    if not require_login(request) or not is_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM requests WHERE id = ?", (req_id,))
    conn.commit()
    return RedirectResponse(url="/dashboard", status_code=303)


# ---------- RUN APP ----------
if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
