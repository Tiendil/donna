from donna.domain.ids import FullArtifactId
from donna.world import markdown
from donna.world.templates import render


def parse_artifact(full_id: FullArtifactId, text: str) -> markdown.ArtifactSource:
    markdown_source = render(full_id, text)

    sections = markdown.parse(markdown_source)

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
