from src.Application.ports import IEventPublisher
from src.Application.use_cases import CreateOnlineTestUseCase
from src.Domain.ports import IOnlineTestRepository
from src.Events.domain_events import OnlineTestCreatedEvent
from src.Infrastructure.consumers import (
    GradebookSlotConsumer,
    InMemoryProcessedEventStore,
    NotificationDispatchConsumer,
)
from src.Infrastructure.event_bus_adapter import EventBusPublisherAdapter
from src.Infrastructure.repositories import InMemoryOnlineTestRepository
from src.Messaging.event_bus import AsyncInMemoryEventBus, IEventBus
from src.WebAPI.di_container import DIContainer, Lifetime


def build_composition_root() -> DIContainer:
    """
    Композиційний корінь (Composition Root) для ЛР №5 (EDA).
    Реєструє репозиторій, асинхронну шину подій, порт видавця, сховище ідемпотентності та споживачів.
    """
    container = DIContainer()
    shared_logs: list[str] = []

    # Singleton: Спільний журнал логів демонстрації
    container.register(list, factory=lambda _: shared_logs, lifetime=Lifetime.SINGLETON)

    # Singleton: Репозиторій тестів у пам'яті
    container.register(
        IOnlineTestRepository,
        factory=lambda _: InMemoryOnlineTestRepository(),
        lifetime=Lifetime.SINGLETON,
    )

    # Singleton: Сховище оброблених EventId (для гарантії ідемпотентності споживачів)
    container.register(
        InMemoryProcessedEventStore,
        factory=lambda _: InMemoryProcessedEventStore(),
        lifetime=Lifetime.SINGLETON,
    )

    # Singleton: Незалежні споживачі подій
    container.register(
        GradebookSlotConsumer,
        factory=lambda s: GradebookSlotConsumer(
            processed_store=s.resolve(InMemoryProcessedEventStore),
            logs=s.resolve(list),
        ),
        lifetime=Lifetime.SINGLETON,
    )
    container.register(
        NotificationDispatchConsumer,
        factory=lambda s: NotificationDispatchConsumer(
            processed_store=s.resolve(InMemoryProcessedEventStore),
            logs=s.resolve(list),
        ),
        lifetime=Lifetime.SINGLETON,
    )

    # Singleton: Асинхронна In-Memory шина подій із підпискою двох незалежних споживачів
    def create_bus(scope) -> IEventBus:
        bus = AsyncInMemoryEventBus(logs=scope.resolve(list))
        gradebook_consumer = scope.resolve(GradebookSlotConsumer)
        notif_consumer = scope.resolve(NotificationDispatchConsumer)
        bus.subscribe(OnlineTestCreatedEvent, gradebook_consumer.handle)
        bus.subscribe(OnlineTestCreatedEvent, notif_consumer.handle)
        return bus

    container.register(IEventBus, factory=create_bus, lifetime=Lifetime.SINGLETON)

    # Singleton: Адаптер порту IEventPublisher поверх шини подій
    container.register(
        IEventPublisher,
        factory=lambda s: EventBusPublisherAdapter(event_bus=s.resolve(IEventBus)),
        lifetime=Lifetime.SINGLETON,
    )

    # Scoped: Сценарій використання CreateOnlineTestUseCase
    container.register(
        CreateOnlineTestUseCase,
        factory=lambda s: CreateOnlineTestUseCase(
            test_repository=s.resolve(IOnlineTestRepository),
            event_publisher=s.resolve(IEventPublisher),
        ),
        lifetime=Lifetime.SCOPED,
    )

    return container
