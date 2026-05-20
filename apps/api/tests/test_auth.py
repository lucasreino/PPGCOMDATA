from app.auth import get_password_hash, verify_password, create_access_token
from app.models.enums import UserRole
from jose import jwt
from app.config import settings


def test_password_hash_roundtrip():
    hashed = get_password_hash("senha-segura-123")
    assert verify_password("senha-segura-123", hashed)
    assert not verify_password("outra-senha", hashed)


def test_create_access_token_payload():
    token = create_access_token("00000000-0000-0000-0000-000000000001", UserRole.ADMINISTRADOR)
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    assert payload["sub"] == "00000000-0000-0000-0000-000000000001"
    assert payload["role"] == "administrador"
