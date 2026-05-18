from typing import Any

from donna.context.primitives import PrimitivesCache
from donna.domain.python_path import PythonPath
from donna.machine import errors as machine_errors
from donna.machine.tests import make as machine_make
from donna.machine.tests.test_primitives import sample_primitive


def _python_path(value: str) -> PythonPath:
    normalized = PythonPath.normalize_raw_value(value)
    assert normalized is not None
    return PythonPath(normalized)


class TestPrimitivesCache:
    def test_resolve__returns_primitive_from_python_path(self) -> None:
        cache = PrimitivesCache()

        result = cache.resolve(machine_make.PRIMITIVE_PATH)

        assert result.is_ok()
        assert result.unwrap() == sample_primitive

    def test_resolve__uses_cached_primitive_on_repeated_calls(self, mocker: Any) -> None:
        cache = PrimitivesCache()
        assert cache.resolve(machine_make.PRIMITIVE_PATH).is_ok()
        import_module = mocker.patch("donna.context.primitives.importlib.import_module")

        result = cache.resolve(machine_make.PRIMITIVE_PATH)

        assert result.is_ok()
        assert result.unwrap() == sample_primitive
        import_module.assert_not_called()

    def test_resolve__rejects_path_without_attribute_name(self) -> None:
        result = PrimitivesCache().resolve(_python_path("primitive"))

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.PrimitiveInvalidImportPath)
        assert error.import_path == "primitive"

    def test_resolve__reports_not_importable_module(self) -> None:
        result = PrimitivesCache().resolve(_python_path("donna.machine.tests.missing.sample_primitive"))

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.PrimitiveModuleNotImportable)
        assert error.module_path == "donna.machine.tests.missing"

    def test_resolve__reports_missing_primitive_attribute(self) -> None:
        result = PrimitivesCache().resolve(_python_path("donna.machine.tests.test_primitives.missing_primitive"))

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.PrimitiveNotAvailable)
        assert error.import_path == "donna.machine.tests.test_primitives.missing_primitive"
        assert error.module_path == "donna.machine.tests.test_primitives"

    def test_resolve__reports_non_primitive_object(self) -> None:
        result = PrimitivesCache().resolve(_python_path("donna.machine.tests.test_primitives.sample_non_primitive"))

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.PrimitiveNotPrimitive)
        assert error.import_path == "donna.machine.tests.test_primitives.sample_non_primitive"
