from pydantic import BaseModel, EmailStr, Field
from app.models.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole

    @classmethod
    def from_user(cls, user) -> "UserPublic":
        return cls(
            id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
        )
