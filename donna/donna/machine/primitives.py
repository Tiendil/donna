import importlib
from typing import TYPE_CHECKING, Any, ClassVar, Iterable

from jinja2.runtime import Context

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import ArtifactSectionId, PythonImportPath
from donna.machine import errors as machine_errors
from donna.machine.artifacts import ArtifactSectionConfig

if TYPE_CHECKING:
    from donna.machine.artifacts import Artifact, ArtifactSection
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit
    from donna.world.config import SourceConfig as SourceConfigModel
    from donna.world.config import WorldConfig
    from donna.world.sources.base import SourceConfig as SourceConfigValue
    from donna.world.worlds.base import World


# TODO: Currently is is a kind of God interface. It is convinient for now.
#       However, in future we should move these methods into specific subclasses.
class Primitive(BaseEntity):
    config_class: ClassVar[type[ArtifactSectionConfig]] = ArtifactSectionConfig

    def validate_section(self, artifact: "Artifact", section_id: ArtifactSectionId) -> Result[None, ErrorsList]:
        return Ok(None)

    def execute_section(self, task: "Task", unit: "WorkUnit", section: "ArtifactSection") -> Iterable["Change"]:
        raise machine_errors.PrimitiveMethodUnsupported(
            primitive_name=self.__class__.__name__, method_name="execute_section()"
        )

    def apply_directive(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        raise machine_errors.PrimitiveMethodUnsupported(
            primitive_name=self.__class__.__name__, method_name="apply_directive()"
        )

    def construct_world(self, config: "WorldConfig") -> "World":
        raise machine_errors.PrimitiveMethodUnsupported(
            primitive_name=self.__class__.__name__, method_name="construct_world()"
        )

    def construct_source(self, config: "SourceConfigModel") -> "SourceConfigValue":
        raise machine_errors.PrimitiveMethodUnsupported(
            primitive_name=self.__class__.__name__, method_name="construct_source()"
        )


@unwrap_to_error
def resolve_primitive(primitive_id: PythonImportPath | str) -> Result[Primitive, ErrorsList]:  # noqa: CCR001
    if isinstance(primitive_id, PythonImportPath):
        import_path = str(primitive_id)
    else:
        import_path = str(PythonImportPath.parse(primitive_id).unwrap())

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
