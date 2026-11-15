# 1. Архітектурна модель C4 (Level 1: System Context та Level 2: Container)

## 1.1. C4 Level 1: System Context Diagram (Діаграма системного контексту)

Діаграма демонструє межі системи **Smart Campus & Educational Portal** (`System of Interest`), ролі кінцевих користувачів та інтеграцію із зовнішніми інформаційними системами університету.

```mermaid
flowchart TB
    classDef person fill:#08427B,stroke:#052E56,color:#FFFFFF,rx:8,ry:8
    classDef system fill:#1168BD,stroke:#0B4884,color:#FFFFFF,rx:8,ry:8
    classDef extSystem fill:#999999,stroke:#6B6B6B,color:#FFFFFF,rx:8,ry:8

    student["<b>[Person] Студент</b><br/>Переглядає розклад та оцінки,<br/>подає електронні заяви,<br/>проходить онлайн-тестування"]:::person
    teacher["<b>[Person] Викладач</b><br/>Веде електронний журнал,<br/>створює тести, перевіряє<br/>результати модульного контролю"]:::person
    dean["<b>[Person] Працівник деканату</b><br/>Формує розклад, погоджує<br/>студентські заяви, генерує<br/>екзаменаційні відомості"]:::person

    campus["<b>[Software System]</b><br/><b>Smart Campus & Educational Portal</b><br/>Централізована вебплатформа для управління<br/>освітнім процесом, розкладом, оцінками,<br/>заявами та онлайн-тестуванням"]:::system

    ldap["<b>[External System]</b><br/><b>Університетський LDAP / AD</b><br/>Корпоративний каталог облікових<br/>записів студентів і викладачів"]:::extSystem
    notif["<b>[External System]</b><br/><b>Шлюзи сповіщень (SMTP / Telegram)</b><br/>Доставка листів та миттєвих<br/>повідомлень користувачам"]:::extSystem
    accounting["<b>[External System]</b><br/><b>Бухгалтерська система ЗВО</b><br/>Розрахунок стипендій та облік<br/>контрактної форми навчання"]:::extSystem

    student -->|"Користується порталом<br/>[HTTPS / TLS 1.3]"| campus
    teacher -->|"Керує журналом і тестами<br/>[HTTPS / TLS 1.3]"| campus
    dean -->|"Адмініструє розклад і заяви<br/>[HTTPS / TLS 1.3]"| campus

    campus -->|"Синхронізує облікові дані<br/>[LDAPS / TCP 636]"| ldap
    campus -->|"Надсилає сповіщення<br/>[SMTPS / HTTPS REST]"| notif
    campus -->|"Експортує зведені рейтинги<br/>[HTTPS / JSON API]"| accounting
```

---

## 1.2. C4 Level 2: Container Diagram (Діаграма контейнерів)

Діаграма деталізує внутрішній технологічний стек відповідно до прийнятих архітектурних рішень (`ADR-0001`, `ADR-0002`, `ADR-0003`) із точним зазначенням мережевих протоколів взаємодії (синхронних та асинхронних):
* **Синхронні виклики:** `HTTPS / REST JSON` (клієнт ↔ API Gateway ↔ Modular Monolith), `HTTPS / OIDC (JWT RS256)` (автентифікація через Keycloak), `TCP/IP (PostgreSQL Wire Protocol)` (робота з БД), `TCP/IP (RESP)` (робота з кешем Redis).
* **Асинхронні виклики:** `AMQP 0-9-1` через брокер повідомлень RabbitMQ для відкладеного розсилання сповіщень та фонової генерації PDF-відомостей.

```mermaid
flowchart TB
    classDef person fill:#08427B,stroke:#052E56,color:#FFFFFF,rx:8,ry:8
    classDef container fill:#438DD5,stroke:#2E6295,color:#FFFFFF,rx:6,ry:6
    classDef db fill:#2F74B5,stroke:#1E4E79,color:#FFFFFF,rx:6,ry:6
    classDef broker fill:#D97706,stroke:#92400E,color:#FFFFFF,rx:6,ry:6
    classDef extSystem fill:#999999,stroke:#6B6B6B,color:#FFFFFF,rx:8,ry:8

    user["<b>[Person] Користувач порталу</b><br/>Студент, Викладач або<br/>Працівник деканату"]:::person

    subgraph campus_boundary ["System Boundary: Smart Campus & Educational Portal"]
        direction TB
        web_spa["<b>[Container] Web SPA Application</b><br/><i>React 19, TypeScript, Vite</i><br/>Клієнтський інтерфейс розкладу,<br/>журналу, заяв та тестування"]:::container
        api_gw["<b>[Container] API Gateway / Reverse Proxy</b><br/><i>Nginx / HAProxy</i><br/>Термінація TLS 1.3, балансування<br/>навантаження, Rate Limiting"]:::container
        keycloak["<b>[Container] Identity Provider</b><br/><i>Keycloak (OAuth 2.0 / OIDC)</i><br/>Автентифікація, видача JWT (RS256)<br/>та інтеграція з LDAP"]:::container
        core_api["<b>[Container] Core Backend API (Modular Monolith)</b><br/><i>Python 3.12, FastAPI, Clean Architecture</i><br/>Модулі: Schedule, Gradebook,<br/>E-Requests, Assessment"]:::container
        postgres[("<b>[Container: Database] PostgreSQL 16+</b><br/><i>Primary Relational DB</i><br/>Схеми даних доменів та<br/>незмінний Audit Log (ACID)")]:::db
        redis[("<b>[Container: Cache] Redis 7+ (AOF)</b><br/><i>In-Memory Cache & Buffer</i><br/>Кеш розкладу (TTL 15 хв),<br/>чернетки тестів, JWT Blacklist")]:::db
        rabbitmq[["<b>[Container: Broker] RabbitMQ</b><br/><i>Message Broker</i><br/>Асинхронні черги подій<br/>(GradeUpdated, RequestApproved)"]]:::broker
        worker["<b>[Container] Notification & Export Worker</b><br/><i>Python Background Worker</i><br/>Розсилка сповіщень та фонова<br/>генерація PDF/XLSX відомостей"]:::container
    end

    ldap["<b>[External] Університетський LDAP</b><br/>Корпоративний каталог"]:::extSystem
    gateways["<b>[External] SMTP / Telegram API</b><br/>Канали доставки повідомлень"]:::extSystem

    user -->|"Взаємодіє з UI<br/>[HTTPS / TLS 1.3]"| web_spa
    web_spa -->|"Виконує запити<br/>[HTTPS / REST JSON]"| api_gw
    web_spa -->|"Автентифікація (PKCE)<br/>[HTTPS / OIDC]"| keycloak

    api_gw -->|"Проксіює запити<br/>[HTTP / REST JSON]"| core_api
    core_api -->|"Запит ключів JWKS<br/>[HTTPS / JSON]"| keycloak
    keycloak -->|"Перевірка облікових даних<br/>[LDAPS / TCP 636]"| ldap

    core_api -->|"Читання/запис (ACID)<br/>[TCP/IP: PostgreSQL Wire, 5432]"| postgres
    core_api -->|"Кешування та буферизація<br/>[TCP/IP: RESP, 6379]"| redis

    core_api -.->|"Публікація подій (Async)<br/>[AMQP 0-9-1 / TCP 5672]"| rabbitmq
    worker -.->|"Читання черг (Async)<br/>[AMQP 0-9-1 / TCP 5672]"| rabbitmq
    worker -->|"Вибірка даних для звітів<br/>[TCP/IP: PostgreSQL Wire]"| postgres
    worker -->|"Надсилання повідомлень<br/>[SMTPS / HTTPS REST]"| gateways
```