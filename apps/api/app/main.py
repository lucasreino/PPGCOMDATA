from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import auth, professores, linhas_pesquisa, uploads, validacao

app = FastAPI(
    title="PPGCOMDATA API",
    description="API para o Sistema Web de Gestão e Análise de Indicadores Docentes (PPGCOM)",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
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
        "version": "1.0.0",
        "ai_model": settings.AI_MODEL
    }

# Create base API router
api_router = APIRouter(prefix="/api/v1")

@api_router.get("/status", tags=["Status"])
async def get_status():
    return {
        "database": "configured",
        "storage": settings.STORAGE_PROVIDER,
        "ai_provider": "available" if settings.AI_API_KEY else "not_configured"
    }

# Mount sub-routers
api_router.include_router(auth.router)
api_router.include_router(professores.router)
api_router.include_router(linhas_pesquisa.router)
api_router.include_router(uploads.router)
api_router.include_router(validacao.router)

app.include_router(api_router)

