from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.reference_service import ReferenceService
from app.dtos.reference_dto import ReferenceRequestDTO

router = APIRouter(prefix="/references", tags=["references"])


@router.post("/")
def get_references(
    dto: ReferenceRequestDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReferenceService(db)
    return service.get_references(dto.chat_session_id)
