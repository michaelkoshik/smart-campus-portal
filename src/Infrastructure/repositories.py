from uuid import UUID
from src.Domain.entities import OnlineTest
from src.Domain.ports import IOnlineTestRepository


class InMemoryOnlineTestRepository(IOnlineTestRepository):
    """Інфраструктурна реалізація репозиторію тестів (In-Memory для прототипу без БД)."""

    def __init__(self) -> None:
        self._storage: dict[UUID, OnlineTest] = {}

    def exists_by_title(self, course_id: UUID, title: str) -> bool:
        normalized = title.strip().lower()
        return any(
            t.course_id == course_id and t.title.lower() == normalized
            for t in self._storage.values()
        )

    def save(self, test: OnlineTest) -> None:
        self._storage[test.id] = test

    def get_by_id(self, test_id: UUID) -> OnlineTest | None:
        return self._storage.get(test_id)
