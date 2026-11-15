from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from src.Domain.exceptions import DomainValidationError
from src.Domain.value_objects import DurationMinutes, MaxScore


class TestCategory(str, Enum):
    MODULE_CONTROL = "MODULE_CONTROL"
    PRACTICE_QUIZ = "PRACTICE_QUIZ"
    FINAL_EXAM = "FINAL_EXAM"


@dataclass
class OnlineTest:
    """Доменна сутність онлайн-тесту (має власну ідентичність id та життєвий цикл)."""
    id: UUID
    course_id: UUID
    title: str
    category: TestCategory
    duration: DurationMinutes
    max_score: MaxScore
    is_published: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        course_id: UUID,
        title: str,
        category: TestCategory,
        duration_minutes: int,
        max_score: float,
        created_at: datetime | None = None,
    ) -> "OnlineTest":
        clean_title = (title or "").strip()
        if len(clean_title) < 5 or len(clean_title) > 150:
            raise DomainValidationError("Назва онлайн-тесту повинна містити від 5 до 150 символів.")

        duration_vo = DurationMinutes(duration_minutes)
        score_vo = MaxScore(float(max_score))

        return cls(
            id=uuid4(),
            course_id=course_id,
            title=clean_title,
            category=category,
            duration=duration_vo,
            max_score=score_vo,
            is_published=False,
            created_at=created_at or datetime.now(timezone.utc),
        )

    def publish(self) -> None:
        if self.is_published:
            raise DomainValidationError("Онлайн-тест уже опубліковано.")
        self.is_published = True
