from dataclasses import dataclass
from src.Domain.exceptions import DomainValidationError


@dataclass(frozen=True)
class DurationMinutes:
    """Value Object: тривалість онлайн-тестування у хвилинах (від 5 до 180)."""
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise DomainValidationError("Тривалість тесту має бути цілим числом.")
        if self.value < 5 or self.value > 180:
            raise DomainValidationError("Тривалість тесту має бути в діапазоні від 5 до 180 хвилин.")


@dataclass(frozen=True)
class MaxScore:
    """Value Object: максимальна кількість балів за тест (від 1.0 до 100.0)."""
    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
            raise DomainValidationError("Максимальний бал має бути числовим значенням.")
        if float(self.value) < 1.0 or float(self.value) > 100.0:
            raise DomainValidationError("Максимальний бал за тест має бути від 1.0 до 100.0.")
