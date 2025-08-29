# FastAPI Request App (Upload PDF)

Aplikasi contoh FastAPI + SQLite + Jinja2 untuk manajemen permintaan dengan upload file **PDF**.

## Fitur
- Login sederhana (cookie) dengan role **admin** & **karyawan**.
- Karyawan: ajukan permintaan + upload PDF.
- Admin: lihat semua permintaan, setujui/tolak/hapus.
- File tersimpan di folder `uploaded_files/` dan bisa diakses via `/uploaded_files/<nama_file>`.

## Cara Menjalankan
1. Buat virtualenv (opsional) dan install dependency:
   ```bash
   pip install -r requirements.txt
   ```
2. Jalankan server:
   ```bash
   python main.py
   ```
3. Buka di browser: `http://127.0.0.1:8000/`

## Akun Awal
- Admin: `admin` / `admin123`
- Karyawan: `budi` / `budi123`
- Karyawan: `siti` / `siti123`

## Catatan
- Database SQLite otomatis dibuat pada start (`app.db`).
- File yang diupload disimpan apa adanya (disarankan nanti menambahkan penamaan unik).
