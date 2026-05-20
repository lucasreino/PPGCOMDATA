from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import (
    auth,
    professores,
    linhas_pesquisa,
    uploads,
    validacao,
    analises,
    dossie_apcn,
    dossie_catalog,
    relatorios_projeto,
    lacunas,
)

app = FastAPI(
    title="PPGCOMDATA API",
    description="API para o Sistema Web de Gestão e Análise de Indicadores Docentes (PPGCOM)",
    version="1.1.0"
)

# CORS middleware configuration
_cors_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base healthcheck route
@app.get("/", tags=["Healthcheck"])
async def read_root():
    return {
        "status": "healthy",
        "service": "PPGCOMDATA Backend API",
        "version": "1.1.0",
        "ai_provider": settings.AI_PROVIDER if settings.AI_API_KEY else None,
        "ai_model": settings.AI_MODEL if settings.AI_API_KEY else None,
    }

# Create base API router
api_router = APIRouter(prefix="/api/v1")

@api_router.get("/status", tags=["Status"])
async def get_status():
    return {
        "version": "1.1.0",
        "database": "configured",
        "storage": settings.STORAGE_PROVIDER,
        "ai_provider": settings.AI_PROVIDER if settings.AI_API_KEY else "not_configured",
        "ai_model": settings.AI_MODEL if settings.AI_API_KEY else None,
    }

# Mount sub-routers
api_router.include_router(auth.router)
api_router.include_router(professores.router)
api_router.include_router(linhas_pesquisa.router)
api_router.include_router(uploads.router)
api_router.include_router(validacao.router)
api_router.include_router(analises.router)
api_router.include_router(dossie_apcn.router)
api_router.include_router(dossie_catalog.router)
api_router.include_router(relatorios_projeto.router)
api_router.include_router(lacunas.router)

app.include_router(api_router)
