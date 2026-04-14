from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.auth_service import AuthService
from app.dtos.user_dto import UserCreateDTO, UserLoginDTO, AuthResponseDTO, UserResponseDTO

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponseDTO)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's identity — used by the frontend on page refresh."""
    return UserResponseDTO(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.value,
    )


@router.post("/signup", response_model=AuthResponseDTO)
def signup(dto: UserCreateDTO, db: Session = Depends(get_db)):
    try:
        result = AuthService(db).signup(dto.name, dto.email, dto.password)
        user = result["user"]
        return AuthResponseDTO(
            user=UserResponseDTO(
                id=user.id, name=user.name, email=user.email, role=user.role.value
            ),
            access_token=result["access_token"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponseDTO)
def login(dto: UserLoginDTO, db: Session = Depends(get_db)):
    try:
        result = AuthService(db).login(dto.email, dto.password)
        user = result["user"]
        return AuthResponseDTO(
            user=UserResponseDTO(
                id=user.id, name=user.name, email=user.email, role=user.role.value
            ),
            access_token=result["access_token"],
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
