from src.Application.ports import IEventPublisher
from src.Events.domain_events import DomainEvent
from src.Messaging.event_bus import IEventBus


class EventBusPublisherAdapter(IEventPublisher):
    """Інфраструктурний адаптер порту IEventPublisher поверх шини IEventBus."""

    def __init__(self, event_bus: IEventBus) -> None:
        self._event_bus = event_bus

    async def publish(self, event: DomainEvent) -> None:
        await self._event_bus.publish(event)
