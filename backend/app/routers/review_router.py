from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.spaced_repetition_service import SpacedRepetitionService

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/due")
def get_due_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get concepts that are due for review."""
    service = SpacedRepetitionService(db)
    return {
        "reviews": service.get_due_reviews(current_user.id),
        "stats": service.get_review_stats(current_user.id),
    }
