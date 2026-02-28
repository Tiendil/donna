import importlib
from typing import TYPE_CHECKING

from donna.context.entity_cache import TimedCache, TimedCacheValue
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import PythonImportPath
from donna.machine import errors as machine_errors

if TYPE_CHECKING:
    from donna.machine.primitives import Primitive


class _PrimitiveCacheValue(TimedCacheValue):
    __slots__ = ("primitive",)

    def __init__(self, primitive: "Primitive", loaded_at_ms: int, checked_at_ms: int) -> None:
        super().__init__(loaded_at_ms=loaded_at_ms, checked_at_ms=checked_at_ms)
        self.primitive = primitive


class PrimitivesCache(TimedCache):
    __slots__ = ("_cache",)

    def __init__(self) -> None:
        self._cache: dict[PythonImportPath, _PrimitiveCacheValue] = {}

    @unwrap_to_error
    def resolve(self, primitive_id: PythonImportPath) -> Result["Primitive", ErrorsList]:  # noqa: CCR001
        from donna.machine.primitives import Primitive

        cached = self._cache.get(primitive_id)
        now_ms = self._now_ms()
        if cached is not None and self._is_within_lifetime(cached, now_ms):
            return Ok(cached.primitive)

        import_path_str = str(primitive_id)

        if "." not in import_path_str:
            return Err([machine_errors.PrimitiveInvalidImportPath(import_path=import_path_str)])

        module_path, primitive_name = import_path_str.rsplit(".", maxsplit=1)

        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            return Err([machine_errors.PrimitiveModuleNotImportable(module_path=module_path)])

        try:
            primitive = getattr(module, primitive_name)
        except AttributeError:
            return Err([machine_errors.PrimitiveNotAvailable(import_path=import_path_str, module_path=module_path)])

        if not isinstance(primitive, Primitive):
            return Err([machine_errors.PrimitiveNotPrimitive(import_path=import_path_str)])

        if cached is not None:
            previous_primitive = cached.primitive
            cached.primitive = primitive
            self._mark_checked(cached, now_ms)
            if previous_primitive is not primitive:
                cached.loaded_at_ms = now_ms
        else:
            cached = _PrimitiveCacheValue(primitive=primitive, loaded_at_ms=now_ms, checked_at_ms=now_ms)
            self._cache[primitive_id] = cached

        return Ok(cached.primitive)
