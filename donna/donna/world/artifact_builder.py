from donna.domain.ids import FullArtifactId
from donna.machine.artifacts import Artifact, ArtifactContent
from donna.world.sources import markdown as markdown_sources


def parse_artifact_content(full_id: FullArtifactId, text: str) -> ArtifactContent:
    return markdown_sources.parse_artifact_content(full_id, text)


def construct_artifact_from_content(full_id: FullArtifactId, content: str) -> Artifact:
    return markdown_sources.construct_artifact_from_markdown_source(full_id, content)
