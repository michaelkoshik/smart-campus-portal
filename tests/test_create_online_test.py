import ast
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4
import pytest

from src.Application.dto import CreateOnlineTestCommand
from src.Application.use_cases import CreateOnlineTestUseCase
from src.Domain.exceptions import (
    DomainValidationError,
    DuplicateTestTitleError,
    RepositoryPortError,
)
from src.Domain.ports import IAuditEventPublisher, IOnlineTestRepository


def test_create_online_test_success_persists_and_publishes_audit() -> None:
    """Тест 1: Успішний шлях зберігає зміну через порт репозиторію та публікує подію аудиту."""
    mock_repo = MagicMock(spec=IOnlineTestRepository)
    mock_repo.exists_by_title.return_value = False
    mock_audit = MagicMock(spec=IAuditEventPublisher)

    use_case = CreateOnlineTestUseCase(
        test_repository=mock_repo,
        audit_publisher=mock_audit,
    )
    command = CreateOnlineTestCommand(
        course_id=uuid4(),
        title="Модульний контроль №1: Архітектурні стилі та шаблони",
        category="MODULE_CONTROL",
        duration_minutes=45,
        max_score=25.0,
        actor_id="teacher-101",
    )

    result = use_case.execute(command)

    assert result.title == "Модульний контроль №1: Архітектурні стилі та шаблони"
    assert result.duration_minutes == 45
    assert result.max_score == 25.0
    assert result.is_published is False
    mock_repo.save.assert_called_once()
    mock_audit.publish_test_created.assert_called_once()


def test_create_online_test_domain_validation_failure_does_not_save() -> None:
    """Тест 2: Відхилення за правилом домену (Value Object DurationMinutes) не викликає запис у порт."""
    mock_repo = MagicMock(spec=IOnlineTestRepository)
    mock_repo.exists_by_title.return_value = False
    mock_audit = MagicMock(spec=IAuditEventPublisher)

    use_case = CreateOnlineTestUseCase(
        test_repository=mock_repo,
        audit_publisher=mock_audit,
    )
    invalid_command = CreateOnlineTestCommand(
        course_id=uuid4(),
        title="Валідаційний тест із некоректною тривалістю",
        category="PRACTICE_QUIZ",
        duration_minutes=500,  # Порушення інваріанта: максимум 180 хвилин
        max_score=20.0,
        actor_id="teacher-101",
    )

    with pytest.raises(DomainValidationError):
        use_case.execute(invalid_command)

    mock_repo.save.assert_not_called()
    mock_audit.publish_test_created.assert_not_called()


def test_create_online_test_duplicate_title_rejected_without_saving() -> None:
    """Тест 3: Відхилення дубліката назви тесту в межах дисципліни без виклику save()."""
    mock_repo = MagicMock(spec=IOnlineTestRepository)
    mock_repo.exists_by_title.return_value = True
    mock_audit = MagicMock(spec=IAuditEventPublisher)

    use_case = CreateOnlineTestUseCase(
        test_repository=mock_repo,
        audit_publisher=mock_audit,
    )
    command = CreateOnlineTestCommand(
        course_id=uuid4(),
        title="Модульний контроль №1",
        category="MODULE_CONTROL",
        duration_minutes=60,
        max_score=30.0,
        actor_id="teacher-101",
    )

    with pytest.raises(DuplicateTestTitleError):
        use_case.execute(command)

    mock_repo.save.assert_not_called()
    mock_audit.publish_test_created.assert_not_called()


def test_create_online_test_repository_port_error_propagates_to_caller() -> None:
    """Тест 4: Помилка інфраструктурного порту доходить до сценарію як залежність без прихованих викликів."""
    mock_repo = MagicMock(spec=IOnlineTestRepository)
    mock_repo.exists_by_title.return_value = False
    mock_repo.save.side_effect = RepositoryPortError("Connection timeout to storage port")
    mock_audit = MagicMock(spec=IAuditEventPublisher)

    use_case = CreateOnlineTestUseCase(
        test_repository=mock_repo,
        audit_publisher=mock_audit,
    )
    command = CreateOnlineTestCommand(
        course_id=uuid4(),
        title="Підсумковий іспит з інженерії ПЗ",
        category="FINAL_EXAM",
        duration_minutes=90,
        max_score=40.0,
        actor_id="teacher-101",
    )

    with pytest.raises(RepositoryPortError, match="Connection timeout"):
        use_case.execute(command)

    mock_audit.publish_test_created.assert_not_called()


def test_domain_layer_has_no_outer_or_framework_dependencies() -> None:
    """Тест 5 (Архітектурний): Перевірка правила залежностей — src/Domain не імпортує зовнішні шари та фреймворки."""
    domain_dir = Path("src/Domain")
    forbidden_modules = {"Application", "Infrastructure", "WebAPI", "fastapi", "sqlalchemy", "requests", "httpx"}

    for py_file in domain_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not any(bad in alias.name for bad in forbidden_modules), f"Forbidden import in {py_file}: {alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not any(bad in node.module for bad in forbidden_modules), f"Forbidden import in {py_file}: {node.module}"

