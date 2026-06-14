import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.deps import require_auth_if_enabled
from app.api.routes import (
    app_settings,
    audit,
    auth,
    bulk_import,
    campaigns,
    conversation,
    discovery,
    documents,
    health,
    manual_tasks,
    messages,
    quotes,
    reports,
    research,
    safety,
    sourcing,
    substances,
    suppliers,
    tariff,
)
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import security_headers_middleware, validate_production_settings
from app.db.models import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    validate_production_settings(settings.app_env, settings.secret_key, settings.backend_cors_origins)
    if get_settings().auto_create_tables:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Chemical Sourcing RFQ CRM",
    version="0.1.0",
    description="Legal B2B chemical sourcing, RFQ and supplier CRM MVP.",
    lifespan=lifespan,
)

settings = get_settings()
if settings.allowed_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(security_headers_middleware)

settings = get_settings()
os.makedirs(settings.storage_path, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.storage_path), name="storage")

app.include_router(health.router)
app.include_router(auth.router)
protected_dependencies = [Depends(require_auth_if_enabled)]
app.include_router(substances.router, dependencies=protected_dependencies)
app.include_router(suppliers.router, dependencies=protected_dependencies)
app.include_router(discovery.router, dependencies=protected_dependencies)
app.include_router(campaigns.router, dependencies=protected_dependencies)
app.include_router(conversation.router, dependencies=protected_dependencies)
app.include_router(messages.router, dependencies=protected_dependencies)
app.include_router(quotes.router, dependencies=protected_dependencies)
app.include_router(manual_tasks.router, dependencies=protected_dependencies)
app.include_router(audit.router, dependencies=protected_dependencies)
app.include_router(app_settings.router, dependencies=protected_dependencies)
app.include_router(safety.router)
app.include_router(sourcing.router, dependencies=protected_dependencies)
app.include_router(documents.router, dependencies=protected_dependencies)
app.include_router(bulk_import.router, dependencies=protected_dependencies)
app.include_router(tariff.router, dependencies=protected_dependencies)
app.include_router(reports.router, dependencies=protected_dependencies)
app.include_router(research.router, dependencies=protected_dependencies)
