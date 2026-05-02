import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import routes as api_routes
from app.web import views as web_views
import os

app = FastAPI(title="MCP-Trustchain", description="Deterministic cybersecurity enforcement for MCP tools.", version="1.0.0")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include API and Web routers
app.include_router(api_routes.router, prefix="/api/v1")
app.include_router(web_views.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
