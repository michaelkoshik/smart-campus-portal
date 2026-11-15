from enum import Enum
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class Lifetime(str, Enum):
    TRANSIENT = "Transient"
    SCOPED = "Scoped"
    SINGLETON = "Singleton"


class ServiceScope:
    """Область видимості (Scope) для життєвого циклу Scoped (один екземпляр на HTTP-запит)."""

    def __init__(self, container: "DIContainer") -> None:
        self._container = container
        self._scoped_instances: dict[type, Any] = {}

    def resolve(self, interface: type[T]) -> T:
        return self._container._resolve_internal(interface, self._scoped_instances)


class DIContainer:
    """Легковаговий DI-контейнер із підтримкою Transient, Scoped та Singleton."""

    def __init__(self) -> None:
        self._registrations: dict[type, tuple[Lifetime, Callable[["ServiceScope"], Any]]] = {}
        self._singletons: dict[type, Any] = {}

    def register(
        self,
        interface: type[T],
        factory: Callable[["ServiceScope"], T],
        lifetime: Lifetime,
    ) -> None:
        self._registrations[interface] = (lifetime, factory)

    def create_scope(self) -> ServiceScope:
        return ServiceScope(self)

    def _resolve_internal(self, interface: type[T], scoped_cache: dict[type, Any]) -> T:
        if interface not in self._registrations:
            raise KeyError(f"Залежність {interface.__name__} не зареєстрована у композиційному корені.")

        lifetime, factory = self._registrations[interface]
        scope_wrapper = ServiceScope(self)
        scope_wrapper._scoped_instances = scoped_cache

        if lifetime == Lifetime.SINGLETON:
            if interface not in self._singletons:
                self._singletons[interface] = factory(scope_wrapper)
            return self._singletons[interface]

        if lifetime == Lifetime.SCOPED:
            if interface not in scoped_cache:
                scoped_cache[interface] = factory(scope_wrapper)
            return scoped_cache[interface]

        # Lifetime.TRANSIENT — новий екземпляр на кожне вирішення
        return factory(scope_wrapper)
