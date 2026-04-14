from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.models.chat_session import ChatSession
from app.utils.auth_middleware import get_current_user
from app.services.quiz_service import QuizService
from app.dtos.quiz_dto import QuizGenerateDTO, QuizSubmitDTO

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.post("/generate")
def generate_quiz(
    dto: QuizGenerateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat_session = db.query(ChatSession).filter(
        ChatSession.id == dto.chat_session_id
    ).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    service = QuizService(db)
    try:
        quiz = service.generate_quiz(chat_session, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "id": quiz.id,
        "question_text": quiz.question_text,
        "options_json": quiz.options_json,
        "difficulty": quiz.difficulty,
        "points": quiz.points,
        "hint": quiz.hint,
        "explanation": quiz.explanation,
    }


@router.post("/submit")
def submit_answer(
    dto: QuizSubmitDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = QuizService(db)
    return service.submit_answer(
        quiz_id=dto.quiz_id,
        user_id=current_user.id,
        selected_option=dto.selected_option,
    )
