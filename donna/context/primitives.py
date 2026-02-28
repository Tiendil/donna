import importlib
from typing import TYPE_CHECKING

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import PythonImportPath
from donna.machine import errors as machine_errors

if TYPE_CHECKING:
    from donna.machine.primitives import Primitive


class PrimitivesCache:
    __slots__ = ("_cache",)

    def __init__(self) -> None:
        self._cache: dict[PythonImportPath, "Primitive"] = {}

    @unwrap_to_error
    def resolve(self, primitive_id: PythonImportPath | str) -> Result["Primitive", ErrorsList]:  # noqa: CCR001
        from donna.machine.primitives import Primitive

        if isinstance(primitive_id, PythonImportPath):
            import_path = primitive_id
        else:
            import_path = PythonImportPath.parse(primitive_id).unwrap()

        cached = self._cache.get(import_path)
        if cached is not None:
            return Ok(cached)

        import_path_str = str(import_path)

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

        self._cache[import_path] = primitive
        return Ok(primitive)
