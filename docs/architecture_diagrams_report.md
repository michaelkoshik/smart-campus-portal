# Архітектурне моделювання системи (C4 Model & UML 2.5) — MILESTONE 2

**Проєкт:** Smart Campus & Educational Portal (Варіант № 3)  
**Виконавець:** Кошик Михайло Сергійович, студент гр. 2ПРс  
**Дисципліна:** Інженерія програмного забезпечення  
**Реліз / Git-тег:** `lr2`  

---

## Огляд архітектурних моделей
У межах Лабораторної роботи № 2 (Milestone 2) із використанням підходу **Diagrams as Code (Mermaid.js)** розроблено комплекс візуальних моделей системи **Smart Campus & Educational Portal**, які деталізують архітектурні рішення, зафіксовані у `ADR-0001`, `ADR-0002` та `ADR-0003`:
* [1. C4 Model: System Context & Container Diagrams](diagrams/01_c4_context_and_container.md)
* [2. Статична структура: UML Component & Domain Class Diagrams](diagrams/02_uml_component_and_class.md)
* [3. Динамічна поведінка: UML Sequence & State Machine Diagrams](diagrams/03_uml_sequence_and_state.md)

---

## 1. Архітектурна модель C4 (Level 1: System Context та Level 2: Container)

### 1.1. C4 Level 1: System Context Diagram
Діаграма демонструє межі системи (`System of Interest`), ролі кінцевих користувачів (Студент, Викладач, Працівник деканату) та інтеграцію із зовнішніми системами університету (LDAP/AD, SMTP/Telegram-шлюзи, бухгалтерська система ЗВО).

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

### 1.2. C4 Level 2: Container Diagram
Відображає розподіл контейнерів системи та точні мережеві протоколи взаємодії: синхронні (`HTTPS / REST JSON`, `HTTPS / OIDC`, `TCP/IP: PostgreSQL Wire`, `TCP/IP: RESP`) та асинхронні (`AMQP 0-9-1` через брокер повідомлень RabbitMQ).

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

---

## 2. Статична структура ПЗ (UML Component & Domain Class Diagrams)

### 2.1. UML Component Diagram (C4 Level 3)
Компонентна структура модульного моноліту з відображенням наданих (**Provided** `()`) та запитуваних (**Required** `-(`) інтерфейсів.

```mermaid
flowchart LR
    classDef comp fill:#1E40AF,stroke:#1E3A8A,color:#FFFFFF,rx:6,ry:6
    classDef iface fill:#EFF6FF,stroke:#2563EB,color:#1E3A8A,rx:12,ry:12
    classDef infra fill:#374151,stroke:#111827,color:#FFFFFF,rx:6,ry:6

    i_rest(["() IRestApiController<br/>[HTTPS / REST JSON]"]):::iface
    i_grade(["() IGradebookContract<br/>[In-Memory Domain API]"]):::iface
    i_audit(["() IAuditLogger<br/>[Append-Only Contract]"]):::iface

    subgraph core_monolith ["Component Boundary: Core Backend API (Modular Monolith)"]
        direction TB
        auth_mw["<b><<Component>></b><br/><b>Security & RBAC/ABAC Middleware</b><br/>Валідація JWT (RS256) та прав доступу"]:::comp
        mod_sched["<b><<Component>></b><br/><b>Schedule Module</b><br/>Управління розкладом груп і викладачів"]:::comp
        mod_grade["<b><<Component>></b><br/><b>Gradebook Module</b><br/>Електронний журнал та розрахунок рейтингу"]:::comp
        mod_assess["<b><<Component>></b><br/><b>Assessment Module</b><br/>Онлайн-тестування та автоперевірка"]:::comp
        mod_req["<b><<Component>></b><br/><b>E-Requests Module</b><br/>Маршрутизація та погодження заяв"]:::comp
        mod_audit["<b><<Component>></b><br/><b>Audit Log Component</b><br/>Фіксація змін оцінок і статусів заяв"]:::comp
    end

    r_oidc(["-( IOidcJwksProvider<br/>[Keycloak JWKS]"]):::iface
    r_cache(["-( ICacheBufferStore<br/>[Redis RESP]"]):::iface
    r_db(["-( IRelationalUnitOfWork<br/>[PostgreSQL Wire]"]):::iface
    r_mq(["-( IDomainEventBus<br/>[RabbitMQ AMQP]"]):::iface

    ad_kc["<b>[Adapter] Keycloak Client</b>"]:::infra
    ad_redis["<b>[Adapter] Redis Repository</b>"]:::infra
    ad_pg["<b>[Adapter] PostgreSQL UoW</b>"]:::infra
    ad_mq["<b>[Adapter] RabbitMQ Publisher</b>"]:::infra

    i_rest --- auth_mw
    auth_mw --> mod_sched
    auth_mw --> mod_grade
    auth_mw --> mod_assess
    auth_mw --> mod_req

    mod_assess -- "Required -(" --> i_grade
    i_grade -- "Provided ()" --> mod_grade

    mod_grade -- "Required -(" --> i_audit
    mod_req -- "Required -(" --> i_audit
    i_audit -- "Provided ()" --> mod_audit

    auth_mw --> r_oidc
    r_oidc -.-> ad_kc

    mod_sched --> r_cache
    mod_assess --> r_cache
    r_cache -.-> ad_redis

    mod_sched --> r_db
    mod_grade --> r_db
    mod_assess --> r_db
    mod_req --> r_db
    mod_audit --> r_db
    r_db -.-> ad_pg

    mod_grade --> r_mq
    mod_req --> r_mq
    r_mq -.-> ad_mq
```

### 2.2. UML Domain Class Diagram
Доменна модель із 9 класів зі специфікаторами доступу (`+`, `-`, `#`), типами даних, методами та кратністю зв'язків (`1`, `0..*`, `1..*`).

```mermaid
classDiagram
    direction TB

    class User {
        #id: UUID
        #email: String
        #fullName: String
        #role: UserRole
        #isActive: Boolean
        +authenticate(token: String): Boolean
        +hasPermission(permission: String): Boolean
    }

    class Student {
        -studentCardNumber: String
        -groupCode: String
        -enrollmentYear: Integer
        +getSchedule(week: Integer): List~ScheduleItem~
        +submitRequest(type: RequestType, payload: JSON): StudentRequest
        +startTestAttempt(testId: UUID): TestAttempt
    }

    class Teacher {
        -academicDegree: String
        -departmentName: String
        +assignGrade(studentId: UUID, courseId: UUID, points: Float): GradeRecord
        +publishTest(testId: UUID): Boolean
    }

    class Course {
        -id: UUID
        -code: String
        -title: String
        -credits: Float
        -semester: Integer
        +calculateFinalRating(studentId: UUID): Float
    }

    class GradeRecord {
        -id: UUID
        -points: Float
        -gradeType: GradeType
        -updatedAt: DateTime
        -updatedBy: UUID
        +updatePoints(newPoints: Float, authorId: UUID): void
        +isPassed(): Boolean
    }

    class OnlineTest {
        -id: UUID
        -title: String
        -durationMinutes: Integer
        -maxScore: Float
        -isPublished: Boolean
        +addQuestion(q: Question): void
        +evaluateAttempt(attempt: TestAttempt): Float
    }

    class Question {
        -id: UUID
        -text: String
        -optionsJson: JSON
        -correctHash: String
        -weight: Float
        +validateAnswer(answer: String): Boolean
    }

    class TestAttempt {
        -id: UUID
        -startedAt: DateTime
        -finishedAt: DateTime
        -draftAnswersJson: JSON
        -earnedScore: Float
        -status: AttemptStatus
        +saveDraftAnswer(questionId: UUID, answer: String): void
        +completeAttempt(): Float
    }

    class StudentRequest {
        -id: UUID
        -requestNumber: String
        -type: RequestType
        -status: RequestStatus
        -createdAt: DateTime
        +submit(): void
        +approve(reviewerId: UUID, comment: String): void
        +reject(reviewerId: UUID, reason: String): void
    }

    User <|-- Student : успадковує
    User <|-- Teacher : успадковує

    Teacher "1" --> "1..*" Course : викладає
    Student "1" --> "0..*" GradeRecord : отримує
    Course "1" o-- "0..*" GradeRecord : містить оцінки
    Course "1" o-- "0..*" OnlineTest : включає тести

    OnlineTest "1" *-- "1..*" Question : складається з (композиція)
    OnlineTest "1" --> "0..*" TestAttempt : має спроби
    Student "1" --> "0..*" TestAttempt : проходить

    Student "1" --> "0..*" StudentRequest : подає заяви
```

---

## 3. Динамічна поведінка системи (UML Sequence & State Machine Diagrams)

### 3.1. UML Sequence Diagram — Сценарій 1: Проходження модульного онлайн-тестування

```mermaid
sequenceDiagram
    autonumber
    actor Student as Студент
    participant SPA as Web SPA (React)
    participant GW as API Gateway (Nginx)
    participant API as Core Backend API (Assessment)
    participant Redis as Redis 7+ (AOF)
    participant PG as PostgreSQL 16+
    participant MQ as RabbitMQ

    Student->>SPA: Натискає «Розпочати тест»
    SPA->>GW: POST /api/v1/tests/{testId}/attempts (Bearer JWT)
    GW->>API: Проксіює запит

    alt Токен невалідний або термін дії минув
        API-->>GW: 401 Unauthorized
        GW-->>SPA: 401 Unauthorized
        SPA-->>Student: Перенаправлення на сторінку входу (Keycloak)
    else Токен валідний та студент записаний на курс
        API->>PG: INSERT INTO schema_assessment.attempts (status='IN_PROGRESS')
        PG-->>API: attemptId, durationMinutes
        API->>Redis: SET attempt:{attemptId}:meta (TTL = duration + 5m)
        API-->>GW: 201 Created (attemptId, questions)
        GW-->>SPA: 201 Created
        SPA-->>Student: Відображає питання тесту та таймер

        loop Кожні 10 секунд або при виборі відповіді (NFR-04)
            Student->>SPA: Обирає варіант відповіді
            SPA->>API: PATCH /api/v1/attempts/{attemptId}/draft
            API->>Redis: HSET attempt:{attemptId}:answers qId answerJson
            Redis-->>API: OK
            API-->>SPA: 200 OK (draftSavedAt)
        end

        Student->>SPA: Натискає «Завершити тест»
        SPA->>API: POST /api/v1/attempts/{attemptId}/submit
        API->>Redis: HGETALL attempt:{attemptId}:answers
        Redis-->>API: Усі збережені відповіді

        alt Час тестування не перевищено
            API->>API: Розрахунок набраних балів (Domain Logic)
            API->>PG: BEGIN TRANSACTION
            API->>PG: UPDATE attempts SET status='COMPLETED', score=earnedScore
            API->>PG: INSERT/UPDATE schema_gradebook.records (оновлення балу в журналі)
            API->>PG: INSERT INTO schema_audit.logs (фіксація результату)
            API->>PG: COMMIT
            PG-->>API: OK

            opt У студента активовані сповіщення (Email / Telegram)
                API-)MQ: Publish TestCompletedEvent (AMQP 0-9-1)
            end

            API-->>SPA: 200 OK (earnedScore, maxScore)
            SPA-->>Student: Відображає результат тестування
        else Час спроби вичерпано (> durationMinutes)
            API->>PG: UPDATE attempts SET status='EXPIRED'
            API-->>SPA: 409 Conflict (Attempt Expired)
            SPA-->>Student: Повідомлення про завершення часу спроби
        end
    end
```

### 3.2. UML Sequence Diagram — Сценарій 2: Подання та розгляд електронної студентської заяви

```mermaid
sequenceDiagram
    autonumber
    actor Student as Студент
    actor Dean as Працівник деканату
    participant SPA as Web SPA (React)
    participant API as Core Backend API (E-Requests)
    participant PG as PostgreSQL 16+
    participant MQ as RabbitMQ
    participant Worker as Notification & Export Worker

    Student->>SPA: Заповнює форму заяви (напр. довідка про навчання)
    SPA->>API: POST /api/v1/requests (JWT, templateId, formData)
    API->>PG: INSERT INTO schema_requests.requests (status='SUBMITTED')
    API->>PG: INSERT INTO schema_audit.logs (action='REQUEST_CREATED')
    PG-->>API: requestId, requestNumber
    API-)MQ: Publish RequestSubmittedEvent (AMQP 0-9-1)
    API-->>SPA: 201 Created (requestNumber)
    SPA-->>Student: Відображає номер заяви та статус «Подано»

    loop Періодичний опитувач черги сповіщень
        MQ-)Worker: Deliver RequestSubmittedEvent
        Worker-->>Dean: Надсилає повідомлення про нову заяву в черзі деканату
    end

    Dean->>SPA: Відкриває заяву та приймає рішення
    SPA->>API: PATCH /api/v1/requests/{requestId}/decision (JWT DEAN_STAFF)

    alt Заяву погоджено (APPROVED)
        API->>PG: UPDATE requests SET status='APPROVED', reviewerId=deanId
        API->>PG: INSERT INTO schema_audit.logs (action='REQUEST_APPROVED')
        API-)MQ: Publish RequestApprovedEvent (AMQP 0-9-1)
        API-->>SPA: 200 OK (status='APPROVED')
        opt Заява передбачає формування офіційної довідки з QR-кодом
            MQ-)Worker: Deliver RequestApprovedEvent
            Worker->>Worker: Генерація підписаного PDF-документа
            Worker-->>Student: Надсилає готовий PDF-документ на Email / Telegram
        end
    else Заяву відхилено (REJECTED)
        API->>PG: UPDATE requests SET status='REJECTED', rejectReason=reason
        API->>PG: INSERT INTO schema_audit.logs (action='REQUEST_REJECTED')
        API-)MQ: Publish RequestRejectedEvent (AMQP 0-9-1)
        API-->>SPA: 200 OK (status='REJECTED')
        MQ-)Worker: Deliver RequestRejectedEvent
        Worker-->>Student: Надсилає сповіщення із причиною відхилення
    end
```

### 3.3. UML State Machine Diagram — Життєвий цикл сутності `StudentRequest`

```mermaid
stateDiagram-v2
    [*] --> Draft : Студент створює заяву

    Draft --> Draft : Автозбереження чернетки [кожні 10 с]
    Draft --> Cancelled : Студент видаляє чернетку
    Draft --> Submitted : Студент натискає «Подати» [валідація полів OK]

    Submitted --> InReview : Працівник деканату бере заяву в роботу
    Submitted --> Cancelled : Студент відкликає заяву [до початку розгляду]

    state InReview {
        [*] --> CheckingData : Перевірка академічних даних
        CheckingData --> NeedClarification : Виявлено неточності в документах
        NeedClarification --> CheckingData : Студент додає виправлені дані
        CheckingData --> ReadyForDecision : Дані підтверджено
    }

    InReview --> Approved : Деканат погоджує заяву [генерація PDF + Audit Log]
    InReview --> Rejected : Деканат відхиляє заяву [із зазначенням причини]

    Approved --> [*]
    Rejected --> [*]
    Cancelled --> [*]
```