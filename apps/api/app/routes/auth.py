from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from app.database import get_session

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
async def login():
    """Placeholder login endpoint."""
    return {"access_token": "mock_jwt_token_here", "token_type": "bearer"}

@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_me():
    return {
        "id": "admin_uuid_placeholder",
        "name": "Coordenador PPGCOM",
        "email": "coordenacao@ppgcom.edu",
        "role": "administrador"
    }
