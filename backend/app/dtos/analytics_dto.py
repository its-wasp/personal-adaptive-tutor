from pydantic import BaseModel


class TopicAnalyticsDTO(BaseModel):
    topic_name: str
    current_level: str
    total_points: int
    quizzes_attempted: int
    quizzes_correct: int
    accuracy_percentage: float


class UserAnalyticsResponseDTO(BaseModel):
    total_topics: int
    total_points: int
    total_quizzes_attempted: int
    total_quizzes_correct: int
    overall_accuracy_percentage: float
    topics: list[TopicAnalyticsDTO]
