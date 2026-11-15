# Architectural Design Document (ADD)
## Система: Smart Campus & Educational Portal (Варіант № 3)

**Студент:** Кошик Михайло Сергійович  
**Група:** 2ПРс (спеціальність 121 / F2 — Інженерія програмного забезпечення)  
**Тег у репозиторії:** `lr6`  
**Посилання на репозиторій:** https://github.com/michaelkoshik/smart-campus-portal/tree/lr6  

---

### 1. Вступ та цілі системи

**Smart Campus & Educational Portal** — це цифрова освітня екосистема вищого навчального закладу (ХНТУ), призначена для автоматизації поточного та підсумкового онлайн-тестування студентів, ведення електронного журналу успішності, обробки електронних заявок деканату та оперативного інформування учасників навчального процесу.

**Ключові бізнес-цілі та зацікавлені сторони (Stakeholders):**
* **Студенти:** складання онлайн-тестів із автозбереженням чернеток відповідей, перегляд результатів та подання заявок до деканату.
* **Викладачі:** створення і публікація модульних контролів, автоматизоване оцінювання та контроль успішності академічних груп.
* **Адміністратори деканату та ІТ-підтримка:** управління ролями, моніторинг доступності сервісів і цілісності журналу оцінок.

---

### 2. Архітектурні обмеження та NFR (ISO/IEC 25010)

**Технологічні та організаційні обмеження:**
* Підтримка вебклієнтів на базі React 19 (SPA) та публічного REST API (OpenAPI 3.0.3).
* Контейнерне розгортання всіх вузлів системи за допомогою Docker Engine та `docker-compose.yml` на університетському Linux-сервері.
* Обов'язкове використання стандартів RFC 7807 (обробка помилок), OAuth 2.0 / OIDC (Keycloak) та гарантії доставки подій `at-least-once` з ідемпотентною обробкою.

**Матриця нефункціональних вимог (ISO 25010) та архітектурного трасування:**

| ID NFR | Характеристика ISO 25010 | Метрика / Цільовий показник | Архітектурне рішення / Вузол забезпечення |
| :--- | :--- | :--- | :--- |
| **NFR-01** | Performance Efficiency | Час відповіді REST API ≤ 200 мс (p95); автозбереження чернетки ≤ 50 мс | In-Memory кешування та буфер чернеток у вузлі `redis-cache` (`ADR-0002`, Розділ 7) |
| **NFR-02** | Reliability & Fault Tolerance | Доступність ≥ 99.5%; відсутність втрати відповідей при обриві зв'язку; ізоляція збоїв споживачів | Асинхронний брокер `rabbitmq-broker` + ідемпотентні воркери `eda-event-worker` (`ADR-0004`) |
| **NFR-03** | Security | Захист трафіку TLS 1.3; рольова авторизація (RBAC) та JWT-токени | Термінація HTTPS на `api-gateway` (`nginx`) + федеративна автентифікація `Keycloak 26 IdP` (`ADR-0003`) |
| **NFR-04** | Maintainability | Ізоляція бізнес-логіки від фреймворків і БД; покриття ядра модульними тестами | 4-шарова Clean Architecture (`src/Domain`, `src/Application`, `src/Infrastructure`, `src/WebAPI`) (`ADR-0001`) |
| **NFR-05** | Compatibility & Interoperability | Строга типізація зовнішніх та внутрішніх контрактів обміну даними | OpenAPI 3.0.3 (`api/openapi.yaml`) та gRPC Proto3 (`api/service.proto`) із економією 41.4% трафіку |

---

### 3. Контекст та межі системи (C4 Level 1)

На рівні системного контексту **Smart Campus & Educational Portal** виступає центральною програмною системою, що взаємодіє з трьома групами користувачів (Студент, Викладач, Адміністратор деканату) та двома зовнішніми інфраструктурними вузлами:
1. **Keycloak 26 IdP (`University SSO Server`)** — зовнішній провайдер ідентичності (OIDC / OAuth 2.0 + PKCE).
2. **External Notification Gateways (`SMTP / Telegram Bot API`)** — зовнішні шлюзи доставки сповіщень.

*(Детальну діаграму контексту зафіксовано у [`docs/architecture_diagrams_report.md`](docs/architecture_diagrams_report.md) та тегу `lr2`).*

---

### 4. Архітектурна стратегія та реєстр ADR

* **`ADR-0001` (Modular Monolith + Clean Architecture):** обрано модульний моноліт із чіткими межами контекстів (`Assessment`, `Gradebook`, `Requests`, `Notifications`) та правилом залежностей всередину (`src/Domain` не має зовнішніх імпортів).
* **`ADR-0002` (Гібридне збереження PostgreSQL 16 + Redis 7):** транзакційні дані оцінок зберігаються в `postgres-db` (ACID), а тимчасові чернетки спроб тестування та ключі ідемпотентності — у `redis-cache`.
* **`ADR-0003` (Централізована автентифікація Keycloak OIDC):** делегування управління обліковими записами та перевірки JWT-токенів зовнішньому IdP.

#### `ADR-0004`: Вибір топології розгортання системи
* **Статус:** Прийнято (Accepted, Milestone 6 / `lr6`).
* **Контекст:** Необхідно розгорнути модульне ядро (`smart-campus-api`), асинхронний обробник подій (`eda-event-worker`), зворотний проксі (`api-gateway`), СУБД (`postgres-db`), кеш (`redis-cache`) та брокер повідомлень (`rabbitmq-broker`) на університетському сервері Ubuntu 24.04 LTS із можливістю простого горизонтального масштабування споживачів подій.
* **Розглянуті варіанти:**
  1. *Розгортання без контейнеризації (Bare-metal systemd)* — складне керування залежностями Python/Nginx/PostgreSQL та ризик конфлікту версій.
  2. *Повноцінний кластер Kubernetes (K8s)* — надлишкова операційна складність (over-engineering) для навантаження одного університету (~2000 активних студентів).
  3. *Контейнерна топологія Docker Engine + Docker Compose (`docker-compose.yml`)* із ізольованою bridge-мережею `campus-net`, винесеним API Gateway (`nginx:1.27-alpine`) та окремим контейнером `eda-event-worker`.
* **Рішення:** Обрано **Варіант 3 (Single-Node Containerized Modular Monolith з винесеними державними вузлами та асинхронним воркером у Docker Compose)**.
* **Наслідки:** Забезпечено відтворюваний запуск усієї інфраструктури однією командою (`docker compose up`), повну ізоляцію внутрішніх портів (`5432`, `6379`, `5672`, `8000`) всередині мережі `campus-net` (назовні відкрито лише `443/HTTPS` на `api-gateway`) та можливість масштабувати `eda-event-worker` командою `docker compose up --scale eda-event-worker=3` без зміни коду.

---

### 5. Структурні діаграми (C4 Level 2/3 та Clean Architecture)

Структурна декомпозиція системи узгоджена між моделями C4 (тег `lr2`) та кодовою базою ядра (теги `lr4`, `lr5`, `lr6`):
* **`src/Domain`** — сутність `OnlineTest`, Value Objects `DurationMinutes` та `MaxScore`, доменні винятки та порти `IOnlineTestRepository`, `IAuditEventPublisher`.
* **`src/Application`** — сценарій використання `CreateOnlineTestUseCase`, DTO (`CreateOnlineTestCommand`, `OnlineTestResultDTO`) та порт видавця подій `IEventPublisher`.
* **`src/Infrastructure`** — реалізації репозиторію (`InMemoryOnlineTestRepository`), адаптера шини (`EventBusPublisherAdapter`) та ідемпотентних споживачів (`GradebookSlotConsumer`, `NotificationDispatchConsumer`) зі сховищем `InMemoryProcessedEventStore`.
* **`src/WebAPI`** — DI-контейнер із життєвими циклами `Singleton`, `Scoped`, `Transient` та композиційний корінь (`composition_root.py`).

---

### 6. Динаміка взаємодії (Специфікації API та Події)

* **Зовнішній REST API ([`api/openapi.yaml`](api/openapi.yaml)):** 6 ендпоінтів (`/tests`, `/tests/{testId}`, `/attempts/{attemptId}/draft`), курсорна пагінація та стандартизовані помилки RFC 7807 (`application/problem+json`).
* **Внутрішній gRPC API ([`api/service.proto`](api/service.proto)):** сервіс `AssessmentGradebookSyncService` (Unary RPC `SyncTestAttemptGrade`, `GetStudentCourseSummary` та Server Streaming RPC `StreamAttemptProgress`). Бенчмарк підтвердив економію 41.4% розміру payload та прискорення серіалізації у 10.76 раза порівняно з JSON.
* **Подійно-орієнтована взаємодія ([`src/Events/domain_events.py`](src/Events/domain_events.py)):** при створенні тесту сценарій `CreateOnlineTestUseCase` публікує незмінну подію `OnlineTestCreatedEvent` через порт `IEventPublisher`. Асинхронна шина `AsyncInMemoryEventBus` доставляє її незалежним споживачам `GradebookSlotConsumer` та `NotificationDispatchConsumer`, які гарантують ідемпотентність через перевірку `event_id`.

---

### 7. Фізична архітектура (UML Deployment Diagram)

Фізичне розміщення компонентів на вузлах інфраструктури описано у файлі [`docs/diagrams/deployment_diagram.puml`](docs/diagrams/deployment_diagram.puml) та візуалізовано на діаграмі [`docs/diagrams/deployment_diagram.png`](docs/diagrams/deployment_diagram.png).

**Узгоджена матриця вузлів, артефактів та мережевих протоколів (`docker-compose.yml` ↔ UML Deployment Diagram):**

| Вузол / Контейнер (`docker-compose.yml`) | Середовище виконання | Артефакт розгортання | Протокол та порт зв'язку |
| :--- | :--- | :--- | :--- |
| `Client Workstation / Mobile` | Web Browser (Chrome/Edge) | `SmartCampus SPA` (React 19) | Вихідний `HTTPS / TLS 1.3 (Port 443)` до `api-gateway` та `Keycloak` |
| `api-gateway` | Docker Engine (`nginx:1.27-alpine`) | `nginx/nginx.conf` | Вхідний `HTTPS (443)`, вихідний `HTTP (8000)` до `smart-campus-api` |
| `smart-campus-api` | Docker Engine (`python:3.12-slim`) | `smart-campus-api:1.0.0` (`src/`) | `HTTP (8000)`, `TCP/5432` (PostgreSQL), `TCP/6379` (Redis), `AMQP/5672` (RabbitMQ) |
| `eda-event-worker` | Docker Engine (`python:3.12-slim`) | `smart-campus-api:1.0.0` (`demo_eda.py`) | `AMQP/5672` (споживання подій), `TCP/5432` (PostgreSQL), `HTTPS/443` (SMTP/Telegram) |
| `postgres-db` | Docker Engine (`postgres:16-alpine`) | База даних `smart_campus` (`pg_data`) | Внутрішній `TCP / PostgreSQL (Port 5432)` у мережі `campus-net` |
| `redis-cache` | Docker Engine (`redis:7-alpine`) | Кеш чернеток та ключів (`redis_data`) | Внутрішній `TCP / RESP (Port 6379)` у мережі `campus-net` |
| `rabbitmq-broker` | Docker Engine (`rabbitmq:3.13-management`) | Обмінник `campus.events` | Внутрішній `AMQP 0-9-1 (Port 5672)`, моніторинг `HTTP (15672)` |

---

### 8. Компроміси та ризики

1. **Modular Monolith замість мікросервісів на старті (`ADR-0001`):** спрощує транзакційну цілісність та розгортання, проте вимагає суворого контролю меж модулів (AST-тести правила залежностей).
2. **Асинхронна доставка `at-least-once` (`ADR-0004`):** забезпечує високу надійність без втрати подій, але створює ризик дублювання повідомлень, який повністю нівелюється обов'язковою перевіркою `event_id` у сховищі оброблених подій перед зміною стану.
3. **Single-Node Docker Compose (`ADR-0004`):** мінімізує витрати на супровід університетського сервера, а при зростанні навантаження дозволяє без зміни бізнес-коду горизонтально масштабувати воркери споживачів або перенести `postgres-db` на керований кластер.
