import asyncio
from uuid import uuid4
from src.Application.dto import CreateOnlineTestCommand
from src.Application.use_cases import CreateOnlineTestUseCase
from src.Events.domain_events import OnlineTestCreatedEvent
from src.Infrastructure.consumers import GradebookSlotConsumer, NotificationDispatchConsumer
from src.Messaging.event_bus import AsyncInMemoryEventBus, IEventBus
from src.WebAPI.composition_root import build_composition_root


async def main() -> None:
    container = build_composition_root()
    scope = container.create_scope()

    use_case = scope.resolve(CreateOnlineTestUseCase)
    bus: AsyncInMemoryEventBus = container.create_scope().resolve(IEventBus)  # type: ignore[assignment]
    gradebook_consumer = scope.resolve(GradebookSlotConsumer)
    notif_consumer = scope.resolve(NotificationDispatchConsumer)
    logs = scope.resolve(list)

    print("=== ЕТАП 1: Сценарій ядра створює тест і публікує подію ===")
    cmd = CreateOnlineTestCommand(
        course_id=uuid4(),
        title="Модульний контроль №2: Подійно-орієнтована архітектура",
        category="MODULE_CONTROL",
        duration_minutes=45,
        max_score=25.0,
        actor_id="teacher-101",
    )
    created_dto = await use_case.execute(cmd)
    await bus.drain()

    print("\n=== ЕТАП 2: Повторна доставка тієї самої події (перевірка ідемпотентності) ===")
    first_slot = gradebook_consumer.created_slots[0]
    # Імітуємо повторну доставку брокером події з тим самим event_id
    duplicate_event = OnlineTestCreatedEvent(
        event_id=list(gradebook_consumer._processed_store._processed)[0][1],
        test_id=created_dto.id,
        course_id=created_dto.course_id,
        title=created_dto.title,
        category=created_dto.category,
        max_score=created_dto.max_score,
        actor_id="teacher-101",
    )
    await bus.publish(duplicate_event)
    await bus.drain()

    print("\n=== ЕТАП 3: Відмовостійкість (падіння одного споживача не зупиняє іншого) ===")
    notif_consumer.simulate_failure = True
    cmd2 = CreateOnlineTestCommand(
        course_id=created_dto.course_id,
        title="Практичний тест: Шаблони мікросервісів",
        category="PRACTICE_QUIZ",
        duration_minutes=30,
        max_score=15.0,
        actor_id="teacher-101",
    )
    await use_case.execute(cmd2)
    await bus.drain()

    for line in logs:
        print(line)

    print("\n=== ПІДСУМКОВИЙ СТАН СПОЖИВАЧІВ ===")
    print(f"Колонок у журналі (GradebookSlotConsumer)      : {len(gradebook_consumer.created_slots)} (очікується 2)")
    print(f"Сповіщень надіслано (NotificationConsumer)     : {len(notif_consumer.sent_notifications)} (очікується 1)")


if __name__ == "__main__":
    asyncio.run(main())
