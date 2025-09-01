import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config.database import Base, engine
from api.auth.routes import router as auth_router
from api.requests.routes import router as requests_router
from api.dashboard.routes import router as dashboard_router
from fastapi.requests import Request
from fastapi.responses import RedirectResponse

APP_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# --- INIT DB ---
Base.metadata.create_all(bind=engine)

# Templates
templates = Jinja2Templates(directory="templates")
app.state.templates = templates

# Static & Uploaded files

UPLOAD_DIR = os.path.join(APP_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploaded_files", StaticFiles(directory="uploaded_files"), name="uploaded_files")

# --- INCLUDE ROUTERS ---
@app.get("/")
async def root(request: Request):
    return RedirectResponse(url="/auth/login")  

app.include_router(auth_router)
app.include_router(requests_router)
app.include_router(dashboard_router)

# --- RUN ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
