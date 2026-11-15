# 3. Динамічна поведінка системи (UML Sequence Diagrams та UML State Machine Diagram)

## 3.1. UML Sequence Diagram — Сценарій 1: Проходження модульного онлайн-тестування

Діаграма моделює процес проходження онлайн-тесту студентом із використанням комбінованих фрагментів UML 2.5:
* **`alt` (Alternative):** перевірка валідності JWT-токена та прав доступу (гілка успіху vs `401 Unauthorized` / `403 Forbidden`), а також перевірка ліміту часу спроби.
* **`loop` (Loop):** періодичне автозбереження чернеток відповідей студента в `Redis 7+` кожні 10 секунд (`NFR-04`, `QAS-1`).
* **`opt` (Optional):** асинхронна публікація події `TestCompletedEvent` у `RabbitMQ` для надсилання сповіщення студенту, якщо у його профілі ввімкнено сповіщення.

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

---

## 3.2. UML Sequence Diagram — Сценарій 2: Подання та розгляд електронної студентської заяви

Діаграма відображає взаємодію студента та працівника деканату під час подання та погодження електронної заяви з використанням фрагментів **`alt`**, **`opt`** та **`loop`**.

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

---

## 3.3. UML State Machine Diagram — Життєвий цикл сутності `StudentRequest` (Електронна заява)

Діаграма станів описує повний життєвий цикл електронної заяви студента в системі **Smart Campus & Educational Portal**: від створення чернетки (`Draft`) до фінальних термінальних станів (`Approved`, `Rejected`, `Cancelled`).

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