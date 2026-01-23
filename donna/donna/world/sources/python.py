from types import ModuleType

from donna.domain.ids import FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import Artifact
from donna.primitives.artifacts import PythonArtifact
from donna.std import artifacts as std_artifacts


def construct_artifact_from_module(module: ModuleType, full_id: FullArtifactId) -> Artifact:
    kind = std_artifacts.python_artifact_kind

    if not isinstance(kind, PythonArtifact):
        raise NotImplementedError("Python artifact kind is not available")

    python_kind_id = FullArtifactLocalId.parse("donna.artifacts.python")
    artifact = kind.construct_module_artifact(module, full_id, python_kind_id)

    if artifact is None:
        raise NotImplementedError(f"Module `{module.__name__}` is not an artifact")

    return artifact
