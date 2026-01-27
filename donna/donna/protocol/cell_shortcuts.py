
from donna.protocol.cells import Cell
from donna.domain.ids import ArtifactLocalId, FullArtifactId, FullArtifactLocalId


def artifact_validation_error(artifact_id: FullArtifactId,
                              message: str) -> Cell:
    return Cell.build(
        kind="artifact_validation_error",
        media_type="text/markdown",
        content=message,
        artifact_id=str(artifact_id))


def artifact_validation_success(artifact_id: FullArtifactId) -> Cell:
    return Cell.build(
        kind="artifact_validation_success",
        media_type="text/markdown",
        content=f"Artifact {artifact_id} validated successfully.",
        artifact_id=str(artifact_id))
