from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.auth import authenticate_user, create_access_token, get_current_user
from app.database import get_session
from app.schemas.auth import TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=token)


@router.post("/logout")
async def logout(_=Depends(get_current_user)):
    return {"message": "Logout realizado com sucesso."}


@router.get("/me", response_model=UserPublic)
async def get_me(current_user=Depends(get_current_user)):
    return UserPublic.from_user(current_user)
