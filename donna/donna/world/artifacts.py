from donna.domain.ids import FullArtifactId
from donna.world import markdown


def parse_artifact(full_id: FullArtifactId, text: str) -> markdown.ArtifactSource:
    sections = markdown.parse(text)

    if not sections:
        raise NotImplementedError("Artifact must have at least one section")

    head = sections[0]
    tail = sections[1:]

    artifact = markdown.ArtifactSource(
        id=full_id,
        head=head,
        tail=tail,
    )

    return artifact
