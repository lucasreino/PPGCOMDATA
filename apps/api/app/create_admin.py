"""Cria ou atualiza o usuário administrador inicial."""

import argparse
import os
import sys

from sqlmodel import Session, select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth import get_password_hash
from app.database import engine
from app.models.core import User
from app.models.enums import UserRole


def create_admin(
    email: str,
    password: str,
    name: str = "Administrador PPGCOM",
    role: UserRole = UserRole.ADMINISTRADOR,
) -> None:
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            existing.name = name
            existing.role = role
            existing.password_hash = get_password_hash(password)
            session.add(existing)
            session.commit()
            print(f"Usuário atualizado: {email} ({role.value})")
            return

        user = User(
            name=name,
            email=email,
            role=role,
            password_hash=get_password_hash(password),
        )
        session.add(user)
        session.commit()
        print(f"Administrador criado: {email} ({role.value})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria usuário administrador do PPGCOMDATA")
    parser.add_argument("--email", default=os.getenv("ADMIN_EMAIL", "admin@ppgcom.edu"))
    parser.add_argument("--password", default=os.getenv("ADMIN_PASSWORD"))
    parser.add_argument("--name", default=os.getenv("ADMIN_NAME", "Administrador PPGCOM"))
    args = parser.parse_args()

    password = args.password
    if not password:
        password = input("Senha do administrador: ").strip()
        if len(password) < 6:
            raise SystemExit("A senha deve ter pelo menos 6 caracteres.")

    create_admin(email=args.email, password=password, name=args.name)


if __name__ == "__main__":
    main()
