from typing import cast

from donna.domain.ids import FullArtifactId, WorldId
from donna.machine.state import State
from donna.std.code.workflows import Workflow
from donna.world import artifacts
from donna.world.config import config


def start() -> None:
    config().get_world(WorldId("session")).initialize(reset=True)

    state = State.build()

    state.save()


def start_workflow(artifact_id: FullArtifactId) -> None:
    workflow = cast(Workflow, artifacts.load_artifact(artifact_id))

    state = State.load()

    state.start_workflow(workflow.full_start_operation_id)

    state.save()
