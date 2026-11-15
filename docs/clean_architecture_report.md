# Звіт про виконання лабораторної роботи №4
## Тема: Модульне ядро, Clean Architecture та Dependency Injection

**Студент:** Кошик Михайло Сергійович  
**Група:** 2ПРс  
**Тег у репозиторії:** `lr4`  
**Посилання на репозиторій:** https://github.com/michaelkoshik/smart-campus-portal/tree/lr4  

---

### 1. Шари та правило залежностей

Проєкт **Smart Campus & Educational Portal** структуровано у чотири ізольовані архітектурні шари з дотриманням правила залежностей (код дивиться виключно всередину):

* **`src/Domain`** (ядро предметної області):
  * `entities.py` — доменна сутність `OnlineTest` (має власну ідентичність `UUID` та бізнес-логіку створення/публікації) і перелік `TestCategory`.
  * `value_objects.py` — незмінні об'єкти-значення `DurationMinutes` (5..180 хв) та `MaxScore` (1.0..100.0), що порівнюються за значенням і містять самовалідацію.
  * `exceptions.py` — спеціалізовані винятки предметної області (`DomainError`, `DomainValidationError`, `DuplicateTestTitleError`, `RepositoryPortError`).
  * `ports.py` — абстрактні інтерфейси (порти) `IOnlineTestRepository` та `IAuditEventPublisher`.
* **`src/Application`** (шар сценаріїв використання — залежить лише від `src/Domain`):
  * `dto.py` — вхідний `CreateOnlineTestCommand` та вихідний `OnlineTestResultDTO`.
  * `use_cases.py` — сценарій `CreateOnlineTestUseCase` із методом `execute()`, який отримує порти через конструктор.
* **`src/Infrastructure`** (шар зовнішніх адаптерів — залежить від `src/Domain`):
  * `repositories.py` — реалізація `InMemoryOnlineTestRepository(IOnlineTestRepository)`.
  * `audit_publisher.py` — реалізація `StructuredAuditEventPublisher(IAuditEventPublisher)`.
* **`src/WebAPI`** (презентаційний шар та композиційний корінь):
  * `di_container.py` — легковий DI-контейнер із підтримкою життєвих циклів `Transient`, `Scoped` та `Singleton`.
  * `composition_root.py` — єдина точка реєстрації всіх залежностей проєкту.
  * `controllers.py` — тонкий контролер `OnlineTestController`, що трансформує вхідний запит у `CreateOnlineTestCommand` та повертає HTTP-відповідь або RFC 7807 Problem Details.

**Підтвердження відсутності зовнішніх залежностей у `src/Domain`:**  
Усі файли шару `src/Domain` використовують виключно стандартну бібліотеку Python (`dataclasses`, `datetime`, `enum`, `uuid`, `abc`). Додатково в наборі тестів реалізовано автоматичний AST-аналізатор (`test_domain_layer_has_no_outer_or_framework_dependencies`), який перевіряє синтаксичне дерево кожного модуля в `src/Domain` та гарантує відсутність імпортів із `Application`, `Infrastructure`, `WebAPI` чи зовнішніх бібліотек.

---

### 2. Сценарій використання

* **Ім'я сценарію:** `CreateOnlineTestUseCase` (`src/Application/use_cases.py`).
* **Порти, що передаються в конструктор (`__init__`):**
  1. `test_repository: IOnlineTestRepository` — порт перевірки унікальності назви та збереження сутності онлайн-тесту.
  2. `audit_publisher: IAuditEventPublisher` — порт публікації події аудиту про створення тесту.
* **Доменні правила, що відхиляють недійсний виклик:**
  * Перевірка унікальності назви тесту в межах навчальної дисципліни (`exists_by_title` → виняток `DuplicateTestTitleError`).
  * Перевірка інваріантів Value Objects: тривалість тесту `DurationMinutes` має бути в діапазоні `[5..180]` хвилин, максимальний бал `MaxScore` — у межах `[1.0..100.0]`, а довжина назви — від 5 до 150 символів (інакше генерується `DomainValidationError` до будь-якого звернення до порту збереження).

---

### 3. Композиційний корінь

Реєстрація сервісів зосереджена в модулі `src/WebAPI/composition_root.py` (`build_composition_root()`):

| Абстракція / Тип | Конкретна реалізація | Життєвий цикл | Обґрунтування вибору життєвого циклу |
| :--- | :--- | :--- | :--- |
| `IOnlineTestRepository` | `InMemoryOnlineTestRepository` | `Singleton` | Сховище в пам'яті (або пул підключень) не зберігає стану конкретного запиту та має жити впродовж усього часу роботи процесу. |
| `IAuditEventPublisher` | `StructuredAuditEventPublisher` | `Singleton` | Stateless-адаптер черги подій; створення одного екземпляра на процес запобігає накладним витратам на повторну ініціалізацію клієнта. |
| `CreateOnlineTestUseCase` | `CreateOnlineTestUseCase` | `Scoped` | Створюється один екземпляр на область видимості одного запиту (Unit of Work), щоб ізолювати стан та контекст виконання окремої операції. |
| `OnlineTestController` | `OnlineTestController` | `Transient` | Тонкий презентаційний контролер не має власного стану між викликами, тому створюється новий легковаговий екземпляр на кожне звернення. |

---

### 4. Модульні тести

У файлі `tests/test_create_online_test.py` реалізовано ізольовані модульні тести без підняття бази даних, мережі чи WebAPI. Зовнішні порти `IOnlineTestRepository` та `IAuditEventPublisher` замінено типізованими замінниками `unittest.mock.MagicMock(spec=...)`:

1. `test_create_online_test_success_persists_and_publishes_audit` — перевіряє успішний сценарій: створення сутності, одноразовий виклик `repository.save()` та публікацію події через `audit_publisher`.
2. `test_create_online_test_domain_validation_failure_does_not_save` — перевіряє відхилення за доменним інваріантом (`duration_minutes = 500 > 180` у `DurationMinutes`) та гарантує, що запис у порт не викликається (`assert_not_called()`).
3. `test_create_online_test_duplicate_title_rejected_without_saving` — перевіряє відхилення при дублюванні назви тесту в межах курсу (`DuplicateTestTitleError`) без виклику `save()`.
4. `test_create_online_test_repository_port_error_propagates_to_caller` — перевіряє коректне прокидання помилки інфраструктурного порту (`RepositoryPortError`) без прихованих звернень до БД.
5. `test_domain_layer_has_no_outer_or_framework_dependencies` — автоматичний AST-тест дотримання правила залежностей шару `src/Domain`.

* **Лог зеленого прогону тестів:** [`docs/pytest_run.log`](pytest_run.log) (`5 passed`).
