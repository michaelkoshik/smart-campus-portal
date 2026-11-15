from uuid import UUID
from src.Application.dto import CreateOnlineTestCommand
from src.Application.use_cases import CreateOnlineTestUseCase
from src.Domain.exceptions import DomainValidationError, DuplicateTestTitleError


class OnlineTestController:
    """
    Тонкий контролер презентаційного шару (WebAPI).
    Не містить бізнес-правил — лише трансформує вхідний словник у Command DTO та формує HTTP-відповідь.
    """

    def __init__(self, create_use_case: CreateOnlineTestUseCase) -> None:
        self._create_use_case = create_use_case

    def post_create_test(self, payload: dict, actor_id: str) -> tuple[int, dict]:
        try:
            command = CreateOnlineTestCommand(
                course_id=UUID(str(payload["course_id"])),
                title=str(payload["title"]),
                category=str(payload["category"]),
                duration_minutes=int(payload["duration_minutes"]),
                max_score=float(payload["max_score"]),
                actor_id=actor_id,
            )
            result = self._create_use_case.execute(command)
            return 201, {
                "id": str(result.id),
                "courseId": str(result.course_id),
                "title": result.title,
                "category": result.category,
                "durationMinutes": result.duration_minutes,
                "maxScore": result.max_score,
                "isPublished": result.is_published,
                "createdAt": result.created_at.isoformat(),
            }
        except (DomainValidationError, DuplicateTestTitleError, KeyError, ValueError) as exc:
            return 422, {
                "type": "https://campus.kntu.edu.ua/probs/validation-error",
                "title": "Unprocessable Entity",
                "status": 422,
                "detail": str(exc),
                "instance": "/api/v1/tests",
            }
