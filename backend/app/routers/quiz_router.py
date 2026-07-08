from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.quiz_service import QuizService
from app.services.errors import NotFoundError
from app.dtos.quiz_dto import (
    QuizGenerateDTO,
    QuizSubmitDTO,
    QuizResponseDTO,
    QuizSubmitResponseDTO,
)

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.post("/generate", response_model=QuizResponseDTO)
def generate_quiz(
    dto: QuizGenerateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QuizService(db)
    try:
        quiz = service.generate_quiz(dto.chat_session_id, user_id=current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # hint and explanation are deliberately absent: both reveal the answer, and
    # the client only needs them in the /quiz/submit response. They used to be
    # returned here, so the answer was readable before the learner picked.
    return {
        "id": quiz.id,
        "question_text": quiz.question_text,
        "options_json": quiz.options_json,
        "difficulty": quiz.difficulty,
        "points": quiz.points,
    }


@router.post("/submit", response_model=QuizSubmitResponseDTO)
def submit_answer(
    dto: QuizSubmitDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QuizService(db)
    try:
        return service.submit_answer(
            quiz_id=dto.quiz_id,
            user_id=current_user.id,
            selected_option=dto.selected_option,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
