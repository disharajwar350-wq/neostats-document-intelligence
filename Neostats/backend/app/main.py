import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api.routes.documents import router as documents_router
from backend.app.repositories.document_repository import DocumentRepository

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)
init_db()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ORIGINS != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(documents_router, prefix=settings.API_V1_STR)

# Setup Frontend Template & Static File Mounts
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CSS_DIR = os.path.join(PROJECT_DIR, "css")
JS_DIR = os.path.join(PROJECT_DIR, "js")
SAMPLES_DIR = os.path.join(PROJECT_DIR, "samples")

if os.path.exists(CSS_DIR):
    app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")
if os.path.exists(JS_DIR):
    app.mount("/js", StaticFiles(directory=JS_DIR), name="js")
if os.path.exists(SAMPLES_DIR):
    app.mount("/samples", StaticFiles(directory=SAMPLES_DIR), name="samples")

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def render_dashboard(request: Request):
    """
    Render main Document Intelligence Dashboard.
    """
    index_path = os.path.join(PROJECT_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>NeoStats Dashboard</h1><p>Visit <a href='/docs'>/docs</a> for API documentation.</p>")

@app.get("/view/{document_name}", response_class=HTMLResponse, tags=["Frontend"])
async def render_document_result(request: Request, document_name: str):
    """
    Render document extraction & validation detail view.
    """
    return HTMLResponse(f"<h1>Document View: {document_name}</h1>")
