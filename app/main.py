import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .config import settings
from .database import init_db
from .api import documents, scenarios, sessions, chat, health

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    _seed_default_scenario()
    from .services.embedding_service import load_model
    load_model()
    from .vector_store import get_collection
    get_collection()
    logger.info("DocMind ready at http://%s:%s", settings.app_host, settings.app_port)
    yield


def _seed_default_scenario():
    from .database import SessionLocal
    from .models.scenario import Scenario
    db = SessionLocal()
    try:
        if db.query(Scenario).count() == 0:
            from .models.scenario import DEFAULT_SYSTEM_PROMPT
            db.add(Scenario(
                name="Trợ lý tài liệu mặc định",
                description="Kịch bản mặc định cho tra cứu tài liệu",
                system_prompt=DEFAULT_SYSTEM_PROMPT,
                is_default=True,
            ))
            db.commit()
    finally:
        db.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.include_router(documents.router, prefix="/api/v1")
app.include_router(scenarios.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def page_chat(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "page": "chat"})


@app.get("/documents", response_class=HTMLResponse)
async def page_documents(request: Request):
    return templates.TemplateResponse("documents.html", {"request": request, "page": "documents"})


@app.get("/scenarios", response_class=HTMLResponse)
async def page_scenarios(request: Request):
    return templates.TemplateResponse("scenarios.html", {"request": request, "page": "scenarios"})
