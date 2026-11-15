from src.Application.dto import CreateOnlineTestCommand, OnlineTestResultDTO
from src.Application.ports import IEventPublisher
from src.Domain.entities import OnlineTest, TestCategory
from src.Domain.exceptions import DomainValidationError, DuplicateTestTitleError
from src.Domain.ports import IOnlineTestRepository
from src.Events.domain_events import OnlineTestCreatedEvent


class CreateOnlineTestUseCase:
    """
    Сценарій використання (Use Case): Створення нового онлайн-тесту.
    Після збереження сутності публікує подію OnlineTestCreatedEvent через абстрактний порт IEventPublisher.
    """

    def __init__(
        self,
        test_repository: IOnlineTestRepository,
        event_publisher: IEventPublisher,
    ) -> None:
        self._test_repository = test_repository
        self._event_publisher = event_publisher

    async def execute(self, command: CreateOnlineTestCommand) -> OnlineTestResultDTO:
        try:
            category_enum = TestCategory(command.category)
        except ValueError as exc:
            raise DomainValidationError(f"Невідома категорія тесту: {command.category}") from exc

        if self._test_repository.exists_by_title(command.course_id, command.title.strip()):
            raise DuplicateTestTitleError(
                f"Тест із назвою '{command.title.strip()}' вже існує в межах обраної дисципліни."
            )

        online_test = OnlineTest.create(
            course_id=command.course_id,
            title=command.title,
            category=category_enum,
            duration_minutes=command.duration_minutes,
            max_score=command.max_score,
        )

        self._test_repository.save(online_test)

        # Публікація незмінної події у минулому часі через порт (без знання транспорту)
        event = OnlineTestCreatedEvent(
            test_id=online_test.id,
            course_id=online_test.course_id,
            title=online_test.title,
            category=online_test.category.value,
            max_score=online_test.max_score.value,
            actor_id=command.actor_id,
        )
        await self._event_publisher.publish(event)

        return OnlineTestResultDTO(
            id=online_test.id,
            course_id=online_test.course_id,
            title=online_test.title,
            category=online_test.category.value,
            duration_minutes=online_test.duration.value,
            max_score=online_test.max_score.value,
            is_published=online_test.is_published,
            created_at=online_test.created_at,
        )
