
from donna.protocol.cells import Cell, MetaValue
from donna.domain.ids import ArtifactLocalId, FullArtifactId, FullArtifactLocalId


def operation_succeeded(message: str, **meta: MetaValue) -> Cell:
    return Cell.build(
        kind="operation_succeeded",
        media_type="text/markdown",
        content=message,
        **meta)
