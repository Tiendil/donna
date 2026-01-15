
from donna.domain.ids import ArtifactKindId, NamespaceId, ArtifactSectionKindId
from donna.machine.artifacts import ArtifactSectionTextKind


text_section_kind = ArtifactSectionTextKind(
    id=ArtifactSectionKindId("text"),
    title="Text Section",
)
