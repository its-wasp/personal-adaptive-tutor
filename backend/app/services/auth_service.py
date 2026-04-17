from sqlalchemy.orm import Session
from app.repositories.user_repo import UserRepository
from app.models.user import User
from app.utils.security import hash_password, verify_password, create_access_token


class AuthService:

    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def signup(self, name: str, email: str, password: str) -> dict:
        existing = self.repo.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
        )
        user = self.repo.create(user)
        token = create_access_token(user.id)

        return {"user": user, "access_token": token}

    def login(self, email: str, password: str) -> dict:
        user = self.repo.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        token = create_access_token(user.id)

        return {"user": user, "access_token": token}
