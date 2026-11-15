# 2. Статична структура ПЗ (UML Component Diagram та UML Domain Class Diagram)

## 2.1. UML Component Diagram (C4 Level 3: Компонентна архітектура Core Backend API)

Діаграма розкриває внутрішній устрій ключового сервісу **Core Backend API (Modular Monolith)** із відображенням доменних модулів (`Schedule`, `Gradebook`, `E-Requests`, `Assessment`), підсистеми аудиту (`Audit Log`) та інфраструктурних адаптерів.
* **Provided Interfaces (Надані інтерфейси `()`)** — публічні REST-контролери та внутрішні контракти модулів (`IScheduleQuery`, `IGradebookCommand`, `IAssessmentService`, `IRequestWorkflow`).
* **Required Interfaces (Запитувані інтерфейси `-(`)** — зовнішні залежності, необхідні компонентам для роботи (`IRedisCache`, `IPostgresRepository`, `IEventPublisher`, `IOidcTokenValidator`).

```mermaid
flowchart LR
    classDef comp fill:#1E40AF,stroke:#1E3A8A,color:#FFFFFF,rx:6,ry:6
    classDef iface fill:#EFF6FF,stroke:#2563EB,color:#1E3A8A,rx:12,ry:12
    classDef infra fill:#374151,stroke:#111827,color:#FFFFFF,rx:6,ry:6

    %% Provided Interfaces (Ball)
    i_rest(["() IRestApiController<br/>[HTTPS / REST JSON]"]):::iface
    i_grade(["() IGradebookContract<br/>[In-Memory Domain API]"]):::iface
    i_audit(["() IAuditLogger<br/>[Append-Only Contract]"]):::iface

    %% Core Components
    subgraph core_monolith ["Component Boundary: Core Backend API (Modular Monolith)"]
        direction TB
        auth_mw["<b><<Component>></b><br/><b>Security & RBAC/ABAC Middleware</b><br/>Валідація JWT (RS256) та прав доступу"]:::comp
        mod_sched["<b><<Component>></b><br/><b>Schedule Module</b><br/>Управління розкладом груп і викладачів"]:::comp
        mod_grade["<b><<Component>></b><br/><b>Gradebook Module</b><br/>Електронний журнал та розрахунок рейтингу"]:::comp
        mod_assess["<b><<Component>></b><br/><b>Assessment Module</b><br/>Онлайн-тестування та автоперевірка"]:::comp
        mod_req["<b><<Component>></b><br/><b>E-Requests Module</b><br/>Маршрутизація та погодження заяв"]:::comp
        mod_audit["<b><<Component>></b><br/><b>Audit Log Component</b><br/>Фіксація змін оцінок і статусів заяв"]:::comp
    end

    %% Required Interfaces (Socket)
    r_oidc(["-( IOidcJwksProvider<br/>[Keycloak JWKS]"]):::iface
    r_cache(["-( ICacheBufferStore<br/>[Redis RESP]"]):::iface
    r_db(["-( IRelationalUnitOfWork<br/>[PostgreSQL Wire]"]):::iface
    r_mq(["-( IDomainEventBus<br/>[RabbitMQ AMQP]"]):::iface

    %% External Adapters
    ad_kc["<b>[Adapter] Keycloak Client</b>"]:::infra
    ad_redis["<b>[Adapter] Redis Repository</b>"]:::infra
    ad_pg["<b>[Adapter] PostgreSQL UoW</b>"]:::infra
    ad_mq["<b>[Adapter] RabbitMQ Publisher</b>"]:::infra

    %% Connections: Provided
    i_rest --- auth_mw
    auth_mw --> mod_sched
    auth_mw --> mod_grade
    auth_mw --> mod_assess
    auth_mw --> mod_req

    %% Inter-module contracts
    mod_assess -- "Required -(" --> i_grade
    i_grade -- "Provided ()" --> mod_grade

    mod_grade -- "Required -(" --> i_audit
    mod_req -- "Required -(" --> i_audit
    i_audit -- "Provided ()" --> mod_audit

    %% Connections: Required to Infra
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

---

## 2.2. UML Domain Class Diagram (Діаграма класів доменної моделі)

Діаграма класів описує 8 ключових сутностей домену **Smart Campus & Educational Portal** із дотриманням усіх вимог UML 2.5:
* **Специфікатори доступу:** `+` (`public`), `-` (`private`), `#` (`protected`).
* **Типи даних** атрибутів та параметрів/результатів методів.
* **Кратність зв'язків (`1`, `0..*`, `1..*`) та семантика відношень:**
  * Успадкування (`<|--`): `Student` та `Teacher` успадковують базовий клас `User`.
  * Композиція (`*--`): `OnlineTest` містить `Question` (питання не існують без тесту); `StudentRequest` містить `RequestHistoryEntry` (історія погодження є невід'ємною частиною заяви).
  * Агрегація (`o--`): `Course` об'єднує записи журналу `GradeRecord` та тести `OnlineTest`.

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