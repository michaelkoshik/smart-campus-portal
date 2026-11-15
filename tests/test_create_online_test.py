import ast
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest

from src.Application.dto import CreateOnlineTestCommand
from src.Application.ports import IEventPublisher
from src.Application.use_cases import CreateOnlineTestUseCase
from src.Domain.exceptions import DomainValidationError
from src.Domain.ports import IOnlineTestRepository
from src.Events.domain_events import OnlineTestCreatedEvent
from src.Infrastructure.consumers import (
    GradebookSlotConsumer,
    InMemoryProcessedEventStore,
    NotificationDispatchConsumer,
)
from src.Messaging.event_bus import AsyncInMemoryEventBus


def test_use_case_publishes_domain_event_via_port() -> None:
    """Тест 1: Сценарій зберігає тест і публікує подію OnlineTestCreatedEvent через абстрактний порт."""
    mock_repo = MagicMock(spec=IOnlineTestRepository)
    mock_repo.exists_by_title.return_value = False
    mock_publisher = AsyncMock(spec=IEventPublisher)

    use_case = CreateOnlineTestUseCase(test_repository=mock_repo, event_publisher=mock_publisher)
    cmd = CreateOnlineTestCommand(
        course_id=uuid4(),
        title="Модульний контроль №2: EDA",
        category="MODULE_CONTROL",
        duration_minutes=45,
        max_score=25.0,
        actor_id="teacher-101",
    )

    result = asyncio.run(use_case.execute(cmd))

    assert result.title == "Модульний контроль №2: EDA"
    mock_repo.save.assert_called_once()
    mock_publisher.publish.assert_awaited_once()
    published_event = mock_publisher.publish.call_args[0][0]
    assert isinstance(published_event, OnlineTestCreatedEvent)
    assert published_event.test_id == result.id


def test_domain_validation_error_does_not_publish_event() -> None:
    """Тест 2: При порушенні інваріанта домену подія не публікується."""
    mock_repo = MagicMock(spec=IOnlineTestRepository)
    mock_repo.exists_by_title.return_value = False
    mock_publisher = AsyncMock(spec=IEventPublisher)

    use_case = CreateOnlineTestUseCase(test_repository=mock_repo, event_publisher=mock_publisher)
    bad_cmd = CreateOnlineTestCommand(
        course_id=uuid4(),
        title="Невалідний тест",
        category="PRACTICE_QUIZ",
        duration_minutes=999,
        max_score=10.0,
        actor_id="teacher-101",
    )

    with pytest.raises(DomainValidationError):
        asyncio.run(use_case.execute(bad_cmd))

    mock_repo.save.assert_not_called()
    mock_publisher.publish.assert_not_awaited()


def test_idempotent_consumers_skip_duplicate_event_delivery() -> None:
    """Тест 3: Повторна доставка події з тим самим EventId пропускається і не змінює стан удруге."""
    async def run_flow() -> None:
        logs: list[str] = []
        store = InMemoryProcessedEventStore()
        c1 = GradebookSlotConsumer(processed_store=store, logs=logs)
        c2 = NotificationDispatchConsumer(processed_store=store, logs=logs)

        bus = AsyncInMemoryEventBus(logs=logs)
        bus.subscribe(OnlineTestCreatedEvent, c1.handle)
        bus.subscribe(OnlineTestCreatedEvent, c2.handle)

        event = OnlineTestCreatedEvent(
            test_id=uuid4(),
            course_id=uuid4(),
            title="Тест на ідемпотентність",
            category="MODULE_CONTROL",
            max_score=20.0,
            actor_id="teacher-101",
        )

        # Перша доставка
        await bus.publish(event)
        await bus.drain()
        # Повторна доставка того самого примірника події (at-least-once)
        await bus.publish(event)
        await bus.drain()

        assert len(c1.created_slots) == 1
        assert len(c2.sent_notifications) == 1
        assert any("DUPLICATE_SKIPPED" in line for line in logs)

    asyncio.run(run_flow())


def test_consumer_failure_is_isolated_from_other_consumers() -> None:
    """Тест 4: Падіння одного споживача не зупиняє іншого і не відкочує роботу видавця."""
    async def run_flow() -> None:
        logs: list[str] = []
        store = InMemoryProcessedEventStore()
        c1 = GradebookSlotConsumer(processed_store=store, logs=logs)
        c2 = NotificationDispatchConsumer(processed_store=store, logs=logs)
        c2.simulate_failure = True

        bus = AsyncInMemoryEventBus(logs=logs)
        bus.subscribe(OnlineTestCreatedEvent, c1.handle)
        bus.subscribe(OnlineTestCreatedEvent, c2.handle)

        event = OnlineTestCreatedEvent(
            test_id=uuid4(),
            course_id=uuid4(),
            title="Тест ізоляції збою",
            category="FINAL_EXAM",
            max_score=40.0,
            actor_id="teacher-101",
        )

        await bus.publish(event)
        await bus.drain()

        assert len(c1.created_slots) == 1
        assert len(c2.sent_notifications) == 0
        assert any("[EventBus][ERROR]" in line for line in logs)

    asyncio.run(run_flow())


def test_application_and_domain_do_not_depend_on_messaging_or_infrastructure() -> None:
    """Тест 5 (Архітектурний): Domain і Application не посилаються на Messaging чи Infrastructure."""
    forbidden = {"Infrastructure", "Messaging", "WebAPI", "pika", "kafka"}
    for layer in ("src/Domain", "src/Application"):
        for py_file in Path(layer).glob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not any(bad in alias.name for bad in forbidden), f"Forbidden import in {py_file}: {alias.name}"
                elif isinstance(node, ast.ImportFrom) and node.module:
                    assert not any(bad in node.module for bad in forbidden), f"Forbidden import in {py_file}: {node.module}"
