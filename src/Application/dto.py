from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CreateOnlineTestCommand:
    """Вхідний DTO сценарію створення онлайн-тесту."""
    course_id: UUID
    title: str
    category: str
    duration_minutes: int
    max_score: float
    actor_id: str


@dataclass(frozen=True)
class OnlineTestResultDTO:
    """Вихідний DTO результату створення онлайн-тесту."""
    id: UUID
    course_id: UUID
    title: str
    category: str
    duration_minutes: int
    max_score: float
    is_published: bool
    created_at: datetime
