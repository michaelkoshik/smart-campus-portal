import threading
from uuid import UUID
from src.Events.domain_events import OnlineTestCreatedEvent


class InMemoryProcessedEventStore:
    """
    Потокобезпечне сховище оброблених подій для забезпечення ідемпотентності споживачів.
    Зберігає пари (consumer_name, event_id).
    """

    def __init__(self) -> None:
        self._processed: set[tuple[str, UUID]] = set()
        self._lock = threading.Lock()

    def is_processed(self, consumer_name: str, event_id: UUID) -> bool:
        with self._lock:
            return (consumer_name, event_id) in self._processed

    def mark_processed(self, consumer_name: str, event_id: UUID) -> None:
        with self._lock:
            self._processed.add((consumer_name, event_id))


class GradebookSlotConsumer:
    """
    Споживач 1: Створює колонку/слот оцінювання в електронному журналі дисципліни.
    Ідемпотентний: перед зміною стану перевіряє event_id у ProcessedEventStore.
    """

    CONSUMER_NAME = "GradebookSlotConsumer"

    def __init__(self, processed_store: InMemoryProcessedEventStore, logs: list[str]) -> None:
        self._processed_store = processed_store
        self._logs = logs
        self.created_slots: list[dict] = []

    async def handle(self, event: OnlineTestCreatedEvent) -> None:
        if self._processed_store.is_processed(self.CONSUMER_NAME, event.event_id):
            self._logs.append(
                f"[{self.CONSUMER_NAME}][DUPLICATE_SKIPPED] Подію event_id={event.event_id} вже оброблено — стан не змінено."
            )
            return

        # Зміна стану (створення колонки журналу) + фіксація event_id
        self.created_slots.append(
            {
                "course_id": str(event.course_id),
                "test_id": str(event.test_id),
                "title": event.title,
                "max_score": event.max_score,
            }
        )
        self._processed_store.mark_processed(self.CONSUMER_NAME, event.event_id)
        self._logs.append(
            f"[{self.CONSUMER_NAME}][PROCESSED] Додано колонку в журнал для тесту '{event.title}' (event_id={event.event_id})."
        )


class NotificationDispatchConsumer:
    """
    Споживач 2: Формує сповіщення студентам групи про створення нового тесту.
    Ідемпотентний та підтримує імітацію збою для перевірки ізоляції споживачів.
    """

    CONSUMER_NAME = "NotificationDispatchConsumer"

    def __init__(self, processed_store: InMemoryProcessedEventStore, logs: list[str]) -> None:
        self._processed_store = processed_store
        self._logs = logs
        self.sent_notifications: list[dict] = []
        self.simulate_failure: bool = False

    async def handle(self, event: OnlineTestCreatedEvent) -> None:
        if self._processed_store.is_processed(self.CONSUMER_NAME, event.event_id):
            self._logs.append(
                f"[{self.CONSUMER_NAME}][DUPLICATE_SKIPPED] Подію event_id={event.event_id} вже оброблено — повторне сповіщення не надіслано."
            )
            return

        if self.simulate_failure:
            # Якщо споживач впав до зміни стану, event_id НЕ позначається як оброблений
            raise RuntimeError("SMTP/Telegram Gateway тимчасово недоступний")

        self.sent_notifications.append(
            {
                "test_id": str(event.test_id),
                "message": f"Додано новий тест: {event.title} (макс. балів: {event.max_score})",
            }
        )
        self._processed_store.mark_processed(self.CONSUMER_NAME, event.event_id)
        self._logs.append(
            f"[{self.CONSUMER_NAME}][PROCESSED] Надіслано сповіщення про тест '{event.title}' (event_id={event.event_id})."
        )
