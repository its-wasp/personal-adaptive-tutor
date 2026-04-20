from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db.session import engine

from app.routers import (
    auth_router,
    chat_router,
    quiz_router,
    feedback_router,
    analytics_router,
    reference_router,
)
from app.routers import knowledge_graph_router, profile_router, onboarding_router, review_router

app = FastAPI(title="Adaptive Learning Platform V1", version="1.0.0")

# CORS — local dev + production origins from env
origins = ["http://localhost:5173", "http://localhost:3000"]
if settings.CORS_ORIGINS:
    origins.extend([o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(quiz_router.router)
app.include_router(feedback_router.router)
app.include_router(analytics_router.router)
app.include_router(reference_router.router)
app.include_router(knowledge_graph_router.router)
app.include_router(profile_router.router)
app.include_router(onboarding_router.router)
app.include_router(review_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
