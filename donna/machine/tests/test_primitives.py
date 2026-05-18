import pytest

from donna.domain.python_path import PythonPath
from donna.machine import errors as machine_errors
from donna.machine.primitives import Primitive, resolve_primitive
from donna.machine.tests import make

sample_primitive = Primitive()
sample_non_primitive = object()


class TestPrimitive:
    def test_validate_section__allows_section_by_default(self) -> None:
        result = sample_primitive.validate_section(make.artifact(), make.PRIMARY_SECTION_ID)

        assert result.is_ok()

    def test_execute_section__raises_unsupported_method(self) -> None:
        with pytest.raises(machine_errors.PrimitiveMethodUnsupported) as exception_info:
            sample_primitive.execute_section(make.task(), make.work_unit(), make.artifact(), make.PRIMARY_SECTION_ID)

        error = exception_info.value
        assert error.arguments == {"primitive_name": "Primitive", "method_name": "execute_section()"}

    def test_apply_directive__raises_unsupported_method(self) -> None:
        with pytest.raises(machine_errors.PrimitiveMethodUnsupported) as exception_info:
            sample_primitive.apply_directive({})

        error = exception_info.value
        assert error.arguments == {"primitive_name": "Primitive", "method_name": "apply_directive()"}


class TestResolvePrimitive:
    def test_success_from_python_path(self) -> None:
        result = resolve_primitive(make.PRIMITIVE_PATH)

        assert result.is_ok()
        assert result.unwrap() == sample_primitive

    def test_invalid_import_path_without_attribute_name(self) -> None:
        result = resolve_primitive(PythonPath("primitive"))

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.PrimitiveInvalidImportPath)
        assert error.import_path == "primitive"

    def test_module_not_importable(self) -> None:
        result = resolve_primitive(PythonPath("donna.machine.tests.missing.sample_primitive"))

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.PrimitiveModuleNotImportable)
        assert error.module_path == "donna.machine.tests.missing"

    def test_primitive_not_available(self) -> None:
        result = resolve_primitive(PythonPath("donna.machine.tests.test_primitives.missing_primitive"))

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.PrimitiveNotAvailable)
        assert error.import_path == "donna.machine.tests.test_primitives.missing_primitive"
        assert error.module_path == "donna.machine.tests.test_primitives"

    def test_object_is_not_primitive(self) -> None:
        result = resolve_primitive(PythonPath("donna.machine.tests.test_primitives.sample_non_primitive"))

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.PrimitiveNotPrimitive)
        assert error.import_path == "donna.machine.tests.test_primitives.sample_non_primitive"
