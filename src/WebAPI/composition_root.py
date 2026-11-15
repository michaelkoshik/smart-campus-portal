from src.Application.use_cases import CreateOnlineTestUseCase
from src.Domain.ports import IAuditEventPublisher, IOnlineTestRepository
from src.Infrastructure.audit_publisher import StructuredAuditEventPublisher
from src.Infrastructure.repositories import InMemoryOnlineTestRepository
from src.WebAPI.controllers import OnlineTestController
from src.WebAPI.di_container import DIContainer, Lifetime


def build_composition_root() -> DIContainer:
    """
    Композиційний корінь (Composition Root).
    Єдине місце в застосунку, де поєднуються абстракції та конкретні реалізації.
    """
    container = DIContainer()

    # 1. Singleton: Сховище In-Memory (або пул підключень/шина подій) без стану конкретного запиту.
    # Обрано Singleton, оскільки об'єкт не зберігає контекст поточного HTTP-запиту і має жити весь час роботи процесу.
    container.register(
        IOnlineTestRepository,
        factory=lambda _: InMemoryOnlineTestRepository(),
        lifetime=Lifetime.SINGLETON,
    )

    # 2. Singleton: Публікатор подій аудиту (stateless адаптер черги повідомлень).
    # Обрано Singleton, щоб не перестворювати клієнт брокера на кожен виклик.
    container.register(
        IAuditEventPublisher,
        factory=lambda _: StructuredAuditEventPublisher(),
        lifetime=Lifetime.SINGLETON,
    )

    # 3. Scoped: Сценарій використання CreateOnlineTestUseCase.
    # Обрано Scoped (один екземпляр на межі одного запиту/Unit of Work), щоб ізолювати контекст виконання запиту.
    container.register(
        CreateOnlineTestUseCase,
        factory=lambda scope: CreateOnlineTestUseCase(
            test_repository=scope.resolve(IOnlineTestRepository),
            audit_publisher=scope.resolve(IAuditEventPublisher),
        ),
        lifetime=Lifetime.SCOPED,
    )

    # 4. Transient: Тонкий контролер OnlineTestController.
    # Обрано Transient (новий екземпляр на кожне звернення), оскільки контролер не має власного стану між запитами.
    container.register(
        OnlineTestController,
        factory=lambda scope: OnlineTestController(
            create_use_case=scope.resolve(CreateOnlineTestUseCase),
        ),
        lifetime=Lifetime.TRANSIENT,
    )

    return container
