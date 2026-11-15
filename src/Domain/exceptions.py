class DomainError(Exception):
    """Базовий виняток предметної області (Domain Layer)."""


class DomainValidationError(DomainError):
    """Порушення інваріантів сутності або Value Object."""


class DuplicateTestTitleError(DomainError):
    """Тест із такою назвою вже існує в межах цієї навчальної дисципліни."""


class RepositoryPortError(DomainError):
    """Помилка інфраструктурного порту збереження даних."""
