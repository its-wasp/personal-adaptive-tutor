from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.onboarding_service import OnboardingService
from app.dtos.onboarding_dto import OnboardingPreferencesDTO, PlacementSubmitDTO

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/status")
def get_onboarding_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if the user has completed onboarding."""
    service = OnboardingService(db)
    profile = service.profile_service.get_or_create_profile(current_user.id)
    return {"onboarding_completed": profile.onboarding_completed}


@router.post("/preferences")
def submit_preferences(
    dto: OnboardingPreferencesDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Step 1: Save learning preferences."""
    service = OnboardingService(db)
    service.submit_preferences(current_user.id, dto.model_dump())
    return {"message": "Preferences saved"}


@router.get("/placement")
def get_placement_quiz(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Step 2: Get the placement quiz questions."""
    service = OnboardingService(db)
    return {"questions": service.get_placement_quiz()}


@router.post("/placement/submit")
def submit_placement(
    dto: PlacementSubmitDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Step 3: Submit placement quiz answers and complete onboarding."""
    service = OnboardingService(db)
    results = service.submit_placement(
        user_id=current_user.id,
        answers=[a.model_dump() for a in dto.answers],
    )
    return results
