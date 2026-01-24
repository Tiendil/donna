from donna.domain.ids import FullArtifactLocalId
from donna.machine.artifacts import Artifact
from donna.machine.operations import FsmMode, OperationMeta


def find_start_operation_id(artifact: Artifact) -> FullArtifactLocalId:
    for section in artifact.sections:
        if not isinstance(section.meta, OperationMeta):
            continue
        if section.meta.fsm_mode != FsmMode.start:
            continue
        if section.id is None:
            raise NotImplementedError(f"Workflow '{artifact.id}' has a start operation without an id.")
        return artifact.id.to_full_local(section.id)

    raise NotImplementedError(f"Workflow '{artifact.id}' does not have a start operation.")
