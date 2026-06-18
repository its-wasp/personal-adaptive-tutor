from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.feedback_service import FeedbackService
from app.services.errors import NotFoundError
from app.dtos.feedback_dto import MessageFeedbackCreateDTO

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/")
def submit_feedback(
    dto: MessageFeedbackCreateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FeedbackService(db)
    try:
        feedback = service.submit_feedback(
            user_id=current_user.id,
            message_id=dto.message_id,
            is_helpful=dto.is_helpful,
            feedback_text=dto.feedback_text,
            feedback_category=dto.feedback_category,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "id": feedback.id,
        "message_id": feedback.message_id,
        "is_helpful": feedback.is_helpful,
        "feedback_text": feedback.feedback_text,
        "feedback_category": feedback.feedback_category,
    }
