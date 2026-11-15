from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Базова незмінна подія предметної області (факт у минулому часі)."""
    event_id: UUID = field(default_factory=uuid4, kw_only=True)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), kw_only=True)


@dataclass(frozen=True)
class OnlineTestCreatedEvent(DomainEvent):
    """Подія: новий онлайн-тест створено викладачем."""
    test_id: UUID
    course_id: UUID
    title: str
    category: str
    max_score: float
    actor_id: str


@dataclass(frozen=True)
class OnlineTestPublishedEvent(DomainEvent):
    """Подія: онлайн-тест опубліковано та відкрито для студентів групи."""
    test_id: UUID
    course_id: UUID
    duration_minutes: int
    published_by: str
