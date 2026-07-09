from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.learner_profile_service import LearnerProfileService
from app.dtos.learner_profile_dto import (
    LearnerPreferencesDTO,
    LearnerProfileResponseDTO,
    PreferencesUpdatedDTO,
)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=LearnerProfileResponseDTO)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LearnerProfileService(db)
    context = service.get_personalization_context(current_user.id)
    # Recomputed on read so the number is current even when the learner hasn't
    # started a new session today. Cheap: one grouped query over their events.
    profile = service.refresh_streak(current_user.id)
    return {
        **context,
        "streak_days": profile.streak_days,
        "longest_streak_days": profile.longest_streak_days,
        "onboarding_completed": profile.onboarding_completed,
    }


@router.put("/me/preferences", response_model=PreferencesUpdatedDTO)
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
