from donna.domain.ids import ArtifactKindId, NamespaceId
from donna.machine.artifacts import PythonArtifact
from donna.std.code.ops import python_module_section_kind

python_artifact_kind = PythonArtifact(
    id=ArtifactKindId("python"),
    namespace_id=NamespaceId("python"),
    description="A Python module artifact.",
    default_section_kind=python_module_section_kind.id,
)
