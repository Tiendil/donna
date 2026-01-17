from donna.domain.ids import ArtifactKindId, ArtifactSectionKindId, NamespaceId
from donna.machine.artifacts import ArtifactSectionTextKind, PythonArtifact, PythonModuleSectionKind

text_section_kind = ArtifactSectionTextKind(
    id=ArtifactSectionKindId("text"),
    title="Text Section",
)


python_module_section_kind = PythonModuleSectionKind(
    id=ArtifactSectionKindId("python_module"),
    title="Python module attribute",
)

python_artifact_kind = PythonArtifact(
    id=ArtifactKindId("python"),
    namespace_id=NamespaceId("python"),
    description="A Python module artifact.",
    default_section_kind=str(python_module_section_kind.id),
)
