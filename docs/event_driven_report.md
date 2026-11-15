@'
# Звіт про виконання лабораторної роботи №5
## Тема: Подійно-орієнтована взаємодія компонентів (EDA)

**Студент:** Кошик Михайло Сергійович  
**Група:** 2ПРс  
**Тег у репозиторії:** `lr5`  
**Посилання на репозиторій:** https://github.com/michaelkoshik/smart-campus-portal/tree/lr5  

---

### 1. Каталог подій

| Подія | Видавець (Publisher) | Споживачі (Subscribers) | Обов'язкові поля та корисне навантаження |
| :--- | :--- | :--- | :--- |
| `OnlineTestCreatedEvent` | `CreateOnlineTestUseCase` (`src/Application`) | `GradebookSlotConsumer`, `NotificationDispatchConsumer` | `event_id: UUID`, `occurred_at: datetime (UTC)`, `test_id: UUID` (агрегат), `course_id: UUID`, `title: str`, `category: str`, `max_score: float`, `actor_id: str` |
| `OnlineTestPublishedEvent` | `PublishOnlineTestUseCase` (`src/Application`) | `NotificationDispatchConsumer`, `ScheduleReminderConsumer` | `event_id: UUID`, `occurred_at: datetime (UTC)`, `test_id: UUID` (агрегат), `course_id: UUID`, `duration_minutes: int`, `published_by: str` |

---

### 2. Транспорт

* **Обраний варіант:** Варіант Б — асинхронна In-Memory шина подій `AsyncInMemoryEventBus` (`src/Messaging/event_bus.py`) на базі `asyncio` та патерну Observer.
* **Обґрунтування вибору:** забезпечує строго асинхронне виконання обробників (через планування окремих задач `asyncio.create_task` із перемиканням контексту поза стеком виклику сценарію видавця), ізоляцію винятків кожного споживача (`try/except`) та високу швидкість виконання тестів без зовнішньої залежності від Docker-демона.
* **Топологія:** **Broker Topology** — шина `AsyncInMemoryEventBus` не містить централізованого оркестратора бізнес-логіки, а лише доставляє незмінну подію всім підписаним споживачам, які самостійно реагують у своїх межах відповідальності.

---

### 3. Видавець і споживачі

* **Видавець:** сценарій використання `CreateOnlineTestUseCase` (`src/Application/use_cases.py`) після збереження сутності `OnlineTest` у репозиторій публікує подію `OnlineTestCreatedEvent` через абстрактний порт `IEventPublisher` (`src/Application/ports.py`), не знаючи про конкретний транспорт.
* **Споживач 1 (`GradebookSlotConsumer`):** створює відповідну колонку (слот оцінювання) в електронному журналі дисципліни.
* **Споживач 2 (`NotificationDispatchConsumer`):** формує та відправляє сповіщення студентам групи про появу нового онлайн-тесту. Падіння цього споживача (`RuntimeError`) перехоплюється шиною і не зупиняє роботу `GradebookSlotConsumer` та не відкочує операцію видавця.

---

### 4. Ідемпотентність

* **Сховище оброблених подій:** потокобезпечне сховище `InMemoryProcessedEventStore` (`src/Infrastructure/consumers.py`), яке зберігає пари `(consumer_name, event_id)`. Перед будь-якою зміною стану споживач викликає `is_processed(...)`, а після успішної зміни фіксує подію через `mark_processed(...)`.
* **Фрагмент логу з пропуском дубліката ([`docs/eda_demo.log`](eda_demo.log)):**

```text
[EventBus] Опубліковано OnlineTestCreatedEvent (event_id=e8b7ad57-a11f-4d26-b8bb-5240c25b8cbe) -> підписників: 2
[GradebookSlotConsumer][PROCESSED] Додано колонку в журнал для тесту 'Модульний контроль №2: Подійно-орієнтована архітектура' (event_id=e8b7ad57-a11f-4d26-b8bb-5240c25b8cbe).
[NotificationDispatchConsumer][PROCESSED] Надіслано сповіщення про тест 'Модульний контроль №2: Подійно-орієнтована архітектура' (event_id=e8b7ad57-a11f-4d26-b8bb-5240c25b8cbe).
[EventBus] Опубліковано OnlineTestCreatedEvent (event_id=e8b7ad57-a11f-4d26-b8bb-5240c25b8cbe) -> підписників: 2
[GradebookSlotConsumer][DUPLICATE_SKIPPED] Подію event_id=e8b7ad57-a11f-4d26-b8bb-5240c25b8cbe вже оброблено — стан не змінено.
[NotificationDispatchConsumer][DUPLICATE_SKIPPED] Подію event_id=e8b7ad57-a11f-4d26-b8bb-5240c25b8cbe вже оброблено — повторне сповіщення не надіслано.