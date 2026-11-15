from datetime import datetime, timezone
from src.Domain.entities import OnlineTest
from src.Domain.ports import IAuditEventPublisher


class StructuredAuditEventPublisher(IAuditEventPublisher):
    """Інфраструктурний адаптер публікації подій аудиту (імітація шини подій RabbitMQ)."""

    def __init__(self) -> None:
        self.events: list[dict] = []

    def publish_test_created(self, test: OnlineTest, actor_id: str) -> None:
        self.events.append(
            {
                "event": "OnlineTestCreated",
                "test_id": str(test.id),
                "course_id": str(test.course_id),
                "actor_id": actor_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
