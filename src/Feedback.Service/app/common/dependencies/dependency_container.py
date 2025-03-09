import inspect
from typing import Type, TypeVar, Callable, Any, Optional

T = TypeVar("T")


class DependencyContainer:
    def __init__(self):
        self._providers: dict[Any, Callable[..., Any]] = {}
        self._singletons: dict[Any, Any] = {}
        self._scoped_instances: dict[Any, Any] = {}

    def register_singleton(self, key: Any, instance: Any) -> None:
        self._singletons[key] = instance

    def register_provider(self, key: Any, provider: Callable[..., Any]) -> None:
        self._providers[key] = provider

    def resolve(self, key: Type[T]) -> Optional[T]:
        if key in self._singletons:
            instance = self._singletons[key]
            if not isinstance(instance, key):
                raise TypeError(
                    f"Instance is not of type {key}, got {type(instance)}")
            return instance

        if key in self._providers:
            provider = self._providers[key]
            sig = inspect.signature(provider)
            kwargs = {}

            for param in sig.parameters.values():
                dependency = None
                if param.annotation != inspect.Parameter.empty:
                    # First try resolving directly using the type annotation
                    dependency = self.resolve(param.annotation)
                    # Fall back to using the annotation's __name__
                    if dependency is None and isinstance(param.annotation, type):
                        dependency = self.resolve(param.annotation.__name__)
                else:
                    dependency = self.resolve(param.name)

                kwargs[param.name] = dependency

            instance = provider(**kwargs)

            if not isinstance(instance, key):
                raise TypeError(
                    f"Instance is not of type {key}, got {type(instance)}")

            return instance

        return None

    def resolve_scoped(self, key: Type[T]) -> Optional[T]:
        if key in self._scoped_instances:
            instance = self._scoped_instances[key]
            if not isinstance(instance, key):
                raise TypeError(
                    f"Instance is not of type {key}, got {type(instance)}")
            return instance
        instance = self.resolve(key)
        if instance is not None:
            self._scoped_instances[key] = instance
        return instance
