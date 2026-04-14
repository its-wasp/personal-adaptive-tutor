from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.learner_profile_service import LearnerProfileService
from app.dtos.learner_profile_dto import LearnerPreferencesDTO

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LearnerProfileService(db)
    context = service.get_personalization_context(current_user.id)
    profile = service.get_or_create_profile(current_user.id)
    return {
        **context,
        "streak_days": profile.streak_days,
        "onboarding_completed": profile.onboarding_completed,
    }


@router.put("/me/preferences")
def update_preferences(
    dto: LearnerPreferencesDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LearnerProfileService(db)
    profile = service.update_preferences(
        current_user.id,
        dto.model_dump(exclude_none=True),
    )
    return {"message": "Preferences updated", "learning_style": profile.learning_style}
