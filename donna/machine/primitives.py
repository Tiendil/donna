import importlib
from typing import TYPE_CHECKING, ClassVar

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import SectionId
from donna.domain.python_path import PythonPath
from donna.machine import errors as machine_errors
from donna.machine.artifacts import ArtifactSectionConfig
from donna.machine.templates_context import DirectiveContext

if TYPE_CHECKING:
    from donna.machine.artifacts import Artifact
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


# TODO: Currently it is a kind of God interface. It is convenient for now.
#       However, in future we should move these methods into specific subclasses.
class Primitive(BaseEntity):
    config_class: ClassVar[type[ArtifactSectionConfig]] = ArtifactSectionConfig

    def validate_section(self, artifact: "Artifact", section_id: SectionId) -> Result[None, ErrorsList]:
        return Ok(None)

    def execute_section(
        self, task: "Task", unit: "WorkUnit", artifact: "Artifact", section_id: SectionId
    ) -> Result[list["Change"], ErrorsList]:
        raise machine_errors.PrimitiveMethodUnsupported(
            primitive_name=self.__class__.__name__, method_name="execute_section()"
        )

    def apply_directive(
        self, context: DirectiveContext, *argv: object, **kwargs: object
    ) -> Result[object, ErrorsList]:
        raise machine_errors.PrimitiveMethodUnsupported(
            primitive_name=self.__class__.__name__, method_name="apply_directive()"
        )


@unwrap_to_error
def resolve_primitive(primitive_id: PythonPath) -> Result[Primitive, ErrorsList]:  # noqa: CCR001
    import_path = str(primitive_id)
    if "." not in import_path:
        return Err([machine_errors.PrimitiveInvalidImportPath(import_path=import_path)])

    module_path, primitive_name = import_path.rsplit(".", maxsplit=1)

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError:
        return Err([machine_errors.PrimitiveModuleNotImportable(module_path=module_path)])

    try:
        primitive = getattr(module, primitive_name)
    except AttributeError:
        return Err([machine_errors.PrimitiveNotAvailable(import_path=import_path, module_path=module_path)])

    if not isinstance(primitive, Primitive):
        return Err([machine_errors.PrimitiveNotPrimitive(import_path=import_path)])

    return Ok(primitive)
