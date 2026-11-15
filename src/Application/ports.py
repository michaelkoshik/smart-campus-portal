from abc import ABC, abstractmethod
from src.Events.domain_events import DomainEvent


class IEventPublisher(ABC):
    """Порт видавця доменних подій у шарі Application (не залежить від транспорту)."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        raise NotImplementedError
