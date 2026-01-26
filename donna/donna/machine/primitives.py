import importlib
from typing import TYPE_CHECKING, Any, ClassVar, Iterable

from jinja2.runtime import Context

from donna.core.entities import BaseEntity
from donna.domain.ids import ArtifactLocalId, PythonImportPath
from donna.machine.artifacts import ArtifactSectionConfig

if TYPE_CHECKING:
    from donna.machine.artifacts import Artifact, ArtifactSection
    from donna.machine.cells import Cell
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

    def execute_section(self, task: "Task", unit: "WorkUnit", section: "ArtifactSection") -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def validate_section(self, artifact: "Artifact", section_id: ArtifactLocalId) -> tuple[bool, list["Cell"]]:
        return True, []

    def apply_directive(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("You MUST implement this method.")

    def construct_world(self, config: "WorldConfig") -> "World":
        raise NotImplementedError("You MUST implement this method.")

    def construct_source(self, config: "SourceConfigModel") -> "SourceConfigValue":
        raise NotImplementedError("You MUST implement this method.")


def resolve_primitive(primitive_id: PythonImportPath | str) -> Primitive:
    if isinstance(primitive_id, PythonImportPath):
        import_path = str(primitive_id)
    else:
        import_path = str(PythonImportPath.parse(primitive_id))

    if "." not in import_path:
        raise NotImplementedError(f"Primitive '{import_path}' is not a valid import path")

    module_path, primitive_name = import_path.rsplit(".", maxsplit=1)

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise NotImplementedError(f"Primitive module '{module_path}' is not importable") from exc

    try:
        primitive = getattr(module, primitive_name)
    except AttributeError as exc:
        raise NotImplementedError(f"Primitive '{import_path}' is not available") from exc

    if not isinstance(primitive, Primitive):
        raise NotImplementedError(f"Primitive '{import_path}' is not a primitive")

    return primitive
