from typing import cast
import contextlib

from donna.domain.ids import FullArtifactId, WorldId
from donna.machine.state import ConsistentState, MutableState
from donna.std.code.workflows import Workflow
from donna.world import artifacts
from donna.world.config import config, World
from donna.domain.ids import ActionRequestId, FullArtifactLocalId, OperationId
from donna.machine.cells import Cell, cell_donna_message


def _session() -> World:
    world = config().get_world(WorldId("session"))

    if not world.is_initialized():
        world.initialize(reset=False)

    return world


def _load_state() -> ConsistentState:
    return ConsistentState.from_json(_session().read_state("state.json").decode("utf-8"))


def _save_state(state: ConsistentState) -> None:
    _session().write_state("state.json", state.to_json().encode("utf-8"))


@contextlib.contextmanager
def _state() -> ConsistentState:
    yield _load_state()


@contextlib.contextmanager
def _state_mutator() -> MutableState:
    mutator = _load_state().mutator()

    try:
        yield mutator
    except Exception as e:
        raise NotImplementedError("Failed to mutate state") from e

    _save_state(mutator.freeze())


def _state_run(mutator: MutableState) -> None:
    while mutator.has_work():
        mutator.step()
        _save_state(mutator.freeze())


def _state_cells() -> list[Cell]:
    with _state() as state:
        return state.get_cells()


def start() -> list[Cell]:
    _session().initialize(reset=True)
    _save_state(MutableState.build().freeze())
    return [cell_donna_message("Started new session.")]


def clear() -> list[Cell]:
    _session().initialize(reset=True)
    return [cell_donna_message("Cleared session.")]


def continue_() -> list[Cell]:
    with _state_mutator() as mutator:
        _state_run(mutator)

    return _state_cells()


def status() -> list[Cell]:
    with _state() as state:
        return state.get_status_cells()


def start_workflow(artifact_id: FullArtifactId) -> list[Cell]:
    workflow = cast(Workflow, artifacts.load_artifact(artifact_id))

    with _state_mutator() as mutator:
        mutator.start_workflow(workflow.full_start_operation_id)
        _save_state(mutator.freeze())
        _state_run(mutator)

    return _state_cells()


def _validate_operation_transition(state: MutableState,
                                   request_id: ActionRequestId,
                                   next_operation_id: FullArtifactLocalId) -> None:
    operation_id = state.get_action_request(request_id).operation_id

    workflow = cast(Workflow, artifacts.load_artifact(operation_id.full_artifact_id))

    operation = workflow.get_operation(cast(OperationId, operation_id.local_id))
    assert operation is not None

    if next_operation_id not in operation.allowed_transtions:
        raise NotImplementedError(f"Operation '{operation_id}' can not go to '{next_operation_id}'")


def complete_action_request(request_id: ActionRequestId, next_operation_id: FullArtifactLocalId) -> list[Cell]:
    with _state_mutator() as mutator:
        _validate_operation_transition(mutator, request_id, next_operation_id)
        mutator.complete_action_request(request_id, next_operation_id)
        _save_state(mutator.freeze())
        _state_run(mutator)

    return _state_cells()
