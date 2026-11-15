# Звіт про виконання лабораторної роботи №3

## Тема: Проєктування та специфікація АРІ (REST OpenAPI 3.0 та gRPC Proto3)

**Студент:** Кошик Михайло Сергійович  
**Група:** 2ПРс  
**Тег у репозиторії:** `lr3`  
**Посилання на репозиторій:** https://github.com/michaelkoshik/smart-campus-portal/tree/lr3  

---

### 1. Архітектурне позиціонування інтерфейсів

У межах наскрізного проєкту **Smart Campus & Educational Portal** (Варіант № 3) спроєктовано два взаємодоповнюючі рівні програмних інтерфейсів за парадигмою **Contract-First**:
* **Публічний REST API (OpenAPI 3.0.3):** призначений для взаємодії клієнтського застосунку `Web SPA (React 19)` та мобільних клієнтів через `API Gateway (Nginx)` із бекендом. Забезпечує кешування на рівні HTTP, зручне налагодження, сумісність із браузерними клієнтами та стандартизовану обробку помилок за **RFC 7807**.
* **Внутрішній gRPC API (Protocol Buffers v3):** призначений для високошвидкісної міжмодульної та міжсервісної взаємодії між модулем тестування (`Assessment Module`), модулем електронного журналу (`Gradebook Module`) та фоновим воркером (`Notification & Export Worker`). Використовує бінарну серіалізацію Protobuf та транспорт **HTTP/2** (мультиплексування потоків, Server Streaming).

---

### 2. Специфікація REST API (OpenAPI 3.0)

* **Специфікація контракту:** [`api/openapi.yaml`](../api/openapi.yaml)
* **Конфігурація лінтера Spectral:** [`.spectral.yaml`](../.spectral.yaml) (`No results with a severity of 'error' found!`)

#### Таблиця ендпоінтів REST API (`/api/v1`)

| HTTP Method | Path | OperationId | Опис операції | Коди відповідей |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/tests` | `listOnlineTests` | Отримання списку онлайн-тестів із фільтрацією (`courseId`, `isPublished`) та курсорною пагінацією (`limit`, `cursor`) | `200 OK`, `400`, `401` |
| `POST` | `/tests` | `createOnlineTest` | Створення нового онлайн-тесту викладачем із валідацією DTO | `201 Created`, `400`, `401`, `422` |
| `GET` | `/tests/{testId}` | `getOnlineTestById` | Отримання детальної інформації про тест за UUID | `200 OK`, `401`, `404` |
| `PATCH` | `/tests/{testId}` | `updateOnlineTest` | Часткове оновлення параметрів або публікація тесту | `200 OK`, `400`, `401`, `404`, `422` |
| `DELETE` | `/tests/{testId}` | `deleteOnlineTest` | Видалення неопублікованого тесту (чернетки) | `204 No Content`, `401`, `404` |
| `PATCH` | `/attempts/{attemptId}/draft` | `saveAttemptDraftAnswer` | Автозбереження проміжної відповіді студента в Redis Buffer | `200 OK`, `400`, `401`, `422` |

#### Застосування стандарту RFC 7807 (Problem Details)
Усі помилки клієнтського (`400 Bad Request`, `401 Unauthorized`, `404 Not Found`, `422 Unprocessable Entity`) та серверного рівнів повертаються із заголовком `Content-Type: application/problem+json` та єдиною типізованою схемою `ProblemDetails` (`type`, `title`, `status`, `detail`, `instance`, `errors`). Це виключає витік внутрішніх стек-трейсів та уніфікує обробку помилок на фронтенді.

#### Верифікація на Prism Mock Server
Локальний мок-сервер запущено командою `npx @stoplight/prism-cli mock api/openapi.yaml -p 4010`. Підтверджено коректну валідацію вхідних запитів:
* `POST /tests` з валідним тілом повертає `201 Created`;
* `POST /tests` з невалідними даними (`courseId: "bad"`, `durationMinutes: 500`) автоматично перехоплюється валідатором і повертає `422 Unprocessable Entity` за стандартом RFC 7807;
* `GET /tests?limit=10&isPublished=true` повертає `200 OK` з об'єктом пагінації `PaginationMeta`.

---

### 3. Специфікація gRPC API (Protocol Buffers v3)

* **Файл контракту Proto3:** [`api/service.proto`](../api/service.proto)
* **Згенеровані Python-стаби (`grpc_tools.protoc`):** [`api/generated/service_pb2.py`](../api/generated/service_pb2.py), [`api/generated/service_pb2_grpc.py`](../api/generated/service_pb2_grpc.py)

Сервіс `smartcampus.assessment.v1.AssessmentGradebookSyncService` визначає 3 типізовані RPC-методи:
1. `SyncTestAttemptGrade (SyncTestGradeRequest) returns (SyncTestGradeResponse)` — **Unary RPC** для атомарної синхронізації нарахованих балів тесту до електронного журналу з передачею вкладеного повідомлення `AuditMetadata` та переліку `AttemptSyncStatus` (зі значенням за замовчуванням `ATTEMPT_SYNC_STATUS_UNSPECIFIED = 0`).
2. `GetStudentCourseSummary (CourseSummaryRequest) returns (CourseSummaryResponse)` — **Unary RPC** для агрегації зведеного рейтингу студента за дисципліною зі списком вкладених повідомлень `repeated TestResultItem` та мітками часу `google.protobuf.Timestamp`.
3. `StreamAttemptProgress (StreamAttemptRequest) returns (stream AttemptProgressEvent)` — **Server Streaming RPC** для трансляції подій проходження тестування групою студентів у реальному часі.

---

### 4. Порівняльний аналіз (JSON vs Protobuf Benchmark)

Експериментальний замір виконано скриптом [`api/benchmark_payload.py`](../api/benchmark_payload.py) на ідентичній сутності `CourseSummaryResponse` (зведений рейтинг із 5 пройденими тестами та метаданими):

| Метрика порівняння | REST / JSON (compact UTF-8) | gRPC / Protocol Buffers v3 | Перевага Protobuf |
| :--- | :---: | :---: | :---: |
| **Розмір серіалізованого payload** | `1463 байт` | `858 байт` | **1.71× компактніше (-41.4% трафіку)** |
| **Час 10 000 серіалізацій (CPU)** | `249.28 мс` | `23.16 мс` | **10.76× швидше** |
| **Людиночитабельність** | Висока (текстовий формат) | Низька (бінарний потік байтів) | JSON зручніший для публічного API |
| **Еволюція схем** | Ручна версійність URL/заголовків | Вбудована через числові теги полів (`1..N`) | Строга Backward/Forward сумісність |
| **Мережевий транспорт** | HTTP/1.1 (Head-of-Line Blocking) | HTTP/2 (Multiplexing, HPACK, Streaming) | Відсутність блокування потоків |

**Інженерний висновок (Trade-offs):** для публічного клієнтського API виправданим є використання **REST / OpenAPI 3.0** (прозорість для браузерів, легке налагодження, кешування), тоді як для внутрішньої синхронізації модулів високої інтенсивності оптимальним є **gRPC / Proto3**, що зменшує мережевий трафік на **41.4%** та знижує навантаження на CPU під час серіалізації більш ніж у **10 разів**.

---

### 5. Висновки

У ході виконання лабораторної роботи № 3 опановано методологію **Contract-First** проєктування розподілених систем (компетентності **ПРН17**, **ФК03**). Створено та провалідовано за допомогою Spectral Linter специфікацію публічного REST API (`api/openapi.yaml`) із підтримкою стандарту помилок RFC 7807, перевірено роботу мок-сервера Prism, спроєктовано бінарний контракт `api/service.proto` (Proto3) зі стрімінгом, згенеровано клієнтсько-серверні стаби та проведено кількісний бенчмарк продуктивності JSON проти Protobuf.