import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Awaitable, Callable, TypeVar
from src.Events.domain_events import DomainEvent

E = TypeVar("E", bound=DomainEvent)
AsyncEventHandler = Callable[[E], Awaitable[None]]


class IEventBus(ABC):
    """Абстрактний контракт шини подій (Observer / Broker Topology)."""

    @abstractmethod
    def subscribe(self, event_type: type[E], handler: AsyncEventHandler[E]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        raise NotImplementedError


class AsyncInMemoryEventBus(IEventBus):
    """
    Асинхронна In-Memory шина подій на базі asyncio та патерну Observer.
    Викликає підписників асинхронно поза стеком виклику сценарію видавця
    та ізолює збої окремих споживачів.
    """

    def __init__(self, logs: list[str] | None = None) -> None:
        self._subscribers: dict[type[DomainEvent], list[AsyncEventHandler]] = defaultdict(list)
        self._pending_tasks: list[asyncio.Task] = []
        self.logs: list[str] = logs if logs is not None else []

    def subscribe(self, event_type: type[E], handler: AsyncEventHandler[E]) -> None:
        self._subscribers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = list(self._subscribers.get(type(event), []))
        self.logs.append(
            f"[EventBus] Опубліковано {type(event).__name__} (event_id={event.event_id}) -> підписників: {len(handlers)}"
        )
        for handler in handlers:
            task = asyncio.create_task(self._dispatch_isolated(handler, event))
            self._pending_tasks.append(task)

    async def _dispatch_isolated(self, handler: AsyncEventHandler, event: DomainEvent) -> None:
        # Асинхронне перемикання контексту, щоб гарантувати вихід зі стеку видавця
        await asyncio.sleep(0)
        try:
            await handler(event)
        except Exception as exc:
            handler_name = getattr(handler, "__qualname__", str(handler))
            self.logs.append(
                f"[EventBus][ERROR] Збій споживача {handler_name} для event_id={event.event_id}: {exc} (інші споживачі та видавець не зачеплені)"
            )

    async def drain(self) -> None:
        """Очікування завершення всіх фонових асинхронних задач доставки."""
        while self._pending_tasks:
            batch = list(self._pending_tasks)
            self._pending_tasks.clear()
            await asyncio.gather(*batch, return_exceptions=True)
