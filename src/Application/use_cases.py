from src.Application.dto import CreateOnlineTestCommand, OnlineTestResultDTO
from src.Domain.entities import OnlineTest, TestCategory
from src.Domain.exceptions import DomainValidationError, DuplicateTestTitleError
from src.Domain.ports import IAuditEventPublisher, IOnlineTestRepository


class CreateOnlineTestUseCase:
    """
    Сценарій використання (Use Case): Створення нового онлайн-тесту.
    Залежності передаються виключно через конструктор (Dependency Injection).
    """

    def __init__(
        self,
        test_repository: IOnlineTestRepository,
        audit_publisher: IAuditEventPublisher,
    ) -> None:
        self._test_repository = test_repository
        self._audit_publisher = audit_publisher

    def execute(self, command: CreateOnlineTestCommand) -> OnlineTestResultDTO:
        # 1. Валідація категорії тесту
        try:
            category_enum = TestCategory(command.category)
        except ValueError as exc:
            raise DomainValidationError(f"Невідома категорія тесту: {command.category}") from exc

        # 2. Перевірка бізнес-правила унікальності назви тесту в межах дисципліни
        if self._test_repository.exists_by_title(command.course_id, command.title.strip()):
            raise DuplicateTestTitleError(
                f"Тест із назвою '{command.title.strip()}' вже існує в межах обраної дисципліни."
            )

        # 3. Створення доменної сутності з перевіркою інваріантів Value Objects
        online_test = OnlineTest.create(
            course_id=command.course_id,
            title=command.title,
            category=category_enum,
            duration_minutes=command.duration_minutes,
            max_score=command.max_score,
        )

        # 4. Збереження через абстрактний порт репозиторію
        self._test_repository.save(online_test)

        # 5. Фіксація події в аудиті через порт публікації
        self._audit_publisher.publish_test_created(online_test, actor_id=command.actor_id)

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
