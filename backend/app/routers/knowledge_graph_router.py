from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.knowledge_graph_service import KnowledgeGraphService

router = APIRouter(prefix="/graph", tags=["knowledge-graph"])


@router.get("/{subject}")
def get_graph(
    subject: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the full knowledge graph for a subject, with user's mastery overlay."""
    service = KnowledgeGraphService(db)
    return service.get_graph_with_mastery(subject, current_user.id)


@router.get("/{subject}/recommend")
def get_recommendation(
    subject: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the next recommended concept to study."""
    service = KnowledgeGraphService(db)
    result = service.get_next_recommended(current_user.id, subject)
    if not result:
        return {"message": "All concepts mastered! No recommendations."}
    return result
