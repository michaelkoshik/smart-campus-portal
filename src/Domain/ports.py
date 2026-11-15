from abc import ABC, abstractmethod
from uuid import UUID
from src.Domain.entities import OnlineTest


class IOnlineTestRepository(ABC):
    """Порт (інтерфейс) репозиторію для збереження та пошуку онлайн-тестів."""

    @abstractmethod
    def exists_by_title(self, course_id: UUID, title: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def save(self, test: OnlineTest) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, test_id: UUID) -> OnlineTest | None:
        raise NotImplementedError


class IAuditEventPublisher(ABC):
    """Порт (інтерфейс) публікації подій аудиту доменних операцій."""

    @abstractmethod
    def publish_test_created(self, test: OnlineTest, actor_id: str) -> None:
        raise NotImplementedError
