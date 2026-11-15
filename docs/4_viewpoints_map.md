# 4. Карта архітектурних ракурсів (ISO/IEC/IEEE 42010:2022)

## 4.1. Концептуальна модель опису архітектури
Відповідно до стандарту **ISO/IEC/IEEE 42010:2022**:
* **Architecture Viewpoint (Архітектурний ракурс)** — це шаблон або специфікація правил, нотації та угод, що визначає, як саме будувати опис системи для вирішення конкретних занепокоєнь (Concerns) певних стейкхолдерів.
* **Architecture View (Архітектурний вигляд)** — це конкретна діаграма або модель, побудована за правилами обраного ракурсу для системи **Smart Campus & Educational Portal**.

## 4.2. Матриця відповідності ракурсів, діаграм та стейкхолдерів

| Viewpoint (Ракурс) | View (Вигляд / Артефакт) | Нотація | Зацікавлені сторони (Stakeholders) | Вирішувані занепокоєння (Concerns) та зміст для порталу |
| :--- | :--- | :--- | :--- | :--- |
| **Context Viewpoint** (Контекстний ракурс) | C4 Level 1: System Context Diagram | C4 Model / PlantUML / Structurizr | Business Owner (Ректорат), End Users (Студенти, Викладачі), Administrative Staff (Деканат) | Визначення меж системи (`System Scope`): взаємодія порталу з користувачами, зовнішнім Identity Provider (Keycloak/LDAP), Email/Telegram-шлюзами та бухгалтерською системою. |
| **Container Viewpoint** (Контейнерний ракурс) | C4 Level 2: Container Diagram | C4 Model / PlantUML | Software Architect, Lead Developer, DevOps / SysAdmin | Розподіл відповідальності між висококорівневими вузлами: Web SPA, API Gateway (Nginx), Modular Monolith API, PostgreSQL 16, Redis 7 та Keycloak. |
| **Structural Viewpoint** (Структурний ракурс) | C4 Level 3: Component Diagram & UML Class Diagram | C4 Model / UML 2.5 | Developers, Module Owners, QA Engineers | Внутрішній устрій модульного моноліту (`Schedule`, `Gradebook`, `E-Requests`, `Assessment`), ізоляція шарів Clean Architecture та доменні сутності. |
| **Behavioral Viewpoint** (Поведінковий ракурс) | UML Sequence Diagram & UML State Machine Diagram | UML 2.5 | Backend Developers, QA Engineers, Security Officer | Динаміка критичних сценаріїв: проходження онлайн-тестування з автозбереженням у Redis (`QAS-1`), авторизація через OIDC (`QAS-3`) та життєвий цикл студентської заяви. |
| **Deployment Viewpoint** (Ракурс розгортання) | UML Deployment Diagram / Infrastructure Diagram | UML 2.5 / C4 Deployment | DevOps / Infrastructure Engineers, Security Officer | Фізична топологія контейнерів Docker, балансування навантаження, політики автомасштабування (`QAS-5`), налаштування TLS 1.3 та резервного копіювання БД (`QAS-2`). |