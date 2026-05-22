import os
from dotenv import load_dotenv

# Load env variables from a .env file if it exists
load_dotenv()

class Settings:
    # Server Configurations
    PORT: int = int(os.getenv("PORT", 8000))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/ppgcomdata"
    )
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    # Authentication
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", 
        "super_secret_jwt_sign_key_for_ppgcomdata_jwt_auth"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440)
    )
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    
    # AI Config (openai | gemini | openai_compatible)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")
    # Fallbacks OpenCode Go quando cota do modelo principal esgota (ordem: pro → flash)
    AI_FALLBACK_MODELS: str = os.getenv(
        "AI_FALLBACK_MODELS", "deepseek-v4-pro,deepseek-v4-flash"
    )
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    AI_REQUEST_DELAY_SECONDS: float = float(os.getenv("AI_REQUEST_DELAY_SECONDS", "0"))
    AI_PARALLEL_WORKERS: int = int(os.getenv("AI_PARALLEL_WORKERS", "3"))
    SECTION_CHUNK_MAX_CHARS: int = int(os.getenv("SECTION_CHUNK_MAX_CHARS", "10000"))
    SECTION_CHUNK_MAX_ITEMS: int = int(os.getenv("SECTION_CHUNK_MAX_ITEMS", "8"))
    
    # Storage Config
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local")
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "ppgcomdata-uploads")
    STORAGE_ACCESS_KEY: str = os.getenv("STORAGE_ACCESS_KEY", "")
    STORAGE_SECRET_KEY: str = os.getenv("STORAGE_SECRET_KEY", "")
    
    # Paths
    UPLOAD_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "uploads"
    )
    # Pasta com XML Lattes ({id_lattes}.xml), ex.: lattes-xml/output
    LATTES_XML_DIR: str = os.getenv("LATTES_XML_DIR", "")

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
