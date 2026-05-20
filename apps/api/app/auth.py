from datetime import datetime, timedelta, timezone
from typing import Optional, Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.config import settings
from app.database import get_session
from app.models.core import User
from app.models.enums import UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, role: UserRole) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": subject,
        "role": role.value,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_uuid = UUID(user_id)
    except (JWTError, ValueError):
        raise credentials_exception

    user = session.get(User, user_uuid)
    if not user:
        raise credentials_exception
    return user


def require_roles(*allowed_roles: UserRole) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente para esta operação.",
            )
        return current_user

    return role_checker


# Roles allowed per area
require_staff = require_roles(
    UserRole.ADMINISTRADOR, UserRole.COORDENACAO, UserRole.SECRETARIA
)
require_admin = require_roles(UserRole.ADMINISTRADOR, UserRole.COORDENACAO)
