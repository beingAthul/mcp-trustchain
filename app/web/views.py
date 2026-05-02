from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

from app import db

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    metrics = db.get_dashboard_metrics()
    return templates.TemplateResponse("dashboard.html", {"request": request, "metrics": metrics})

@router.get("/scanner", response_class=HTMLResponse)
async def scanner(request: Request):
    return templates.TemplateResponse("scanner.html", {"request": request})

@router.get("/registry", response_class=HTMLResponse)
async def registry(request: Request):
    tools = db.get_all_tools()
    return templates.TemplateResponse("registry.html", {"request": request, "tools": tools})

@router.get("/verify", response_class=HTMLResponse)
async def verify(request: Request):
    return templates.TemplateResponse("verify.html", {"request": request})

@router.get("/audit", response_class=HTMLResponse)
async def audit(request: Request):
    logs = db.get_audits()
    return templates.TemplateResponse("audit.html", {"request": request, "logs": logs})
