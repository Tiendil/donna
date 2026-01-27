import contextlib
import functools
from typing import Callable, Iterator, ParamSpec

from donna.domain.ids import ActionRequestId, FullArtifactId, FullArtifactLocalId, WorldId
from donna.machine.operations import OperationMeta
from donna.machine.state import ConsistentState, MutableState
from donna.protocol.cells import Cell, cell_donna_message
from donna.world import artifacts
from donna.world import tmp as world_tmp
from donna.world.config import config
from donna.world.worlds.base import World


def _session() -> World:
    world = config().get_world(WorldId("session"))

    if not world.is_initialized():
        world.initialize(reset=False)

    return world


def _load_state() -> ConsistentState:
    content = _session().read_state("state.json")

    if content is None:
        raise NotImplementedError("Session state is not initialized")

    return ConsistentState.from_json(content.decode("utf-8"))


def _save_state(state: ConsistentState) -> None:
    _session().write_state("state.json", state.to_json().encode("utf-8"))


@contextlib.contextmanager
def _state() -> Iterator[ConsistentState]:
    yield _load_state()


@contextlib.contextmanager
def _state_mutator() -> Iterator[MutableState]:
    mutator = _load_state().mutator()

    try:
        yield mutator
    except Exception as e:
        raise NotImplementedError("Failed to mutate state") from e

    _save_state(mutator.freeze())


def _state_run(mutator: MutableState) -> None:
    while mutator.has_work():
        mutator.exectute_next_work_unit()
        _save_state(mutator.freeze())


def _state_cells() -> list[Cell]:
    with _state() as state:
        return state.get_cells()


P = ParamSpec("P")


def _session_required(func: Callable[P, list[Cell]]) -> Callable[P, list[Cell]]:
    # TODO: refactor to catch domain exception from load_state
    #       when we implement domain exceptions
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[Cell]:
        try:
            _load_state()
        except Exception:
            return [cell_donna_message("No active session. Please start a new session.")]

        return func(*args, **kwargs)

    return wrapper


def start() -> list[Cell]:
    world_tmp.clear()
    _session().initialize(reset=True)
    _save_state(MutableState.build().freeze())
    return [cell_donna_message("Started new session.")]


def clear() -> list[Cell]:
    world_tmp.clear()
    _session().initialize(reset=True)
    return [cell_donna_message("Cleared session.")]


@_session_required
def continue_() -> list[Cell]:
    with _state_mutator() as mutator:
        _state_run(mutator)

    return _state_cells()


@_session_required
def status() -> list[Cell]:
    with _state() as state:
        return state.cells_for_status()


@_session_required
def start_workflow(artifact_id: FullArtifactId) -> list[Cell]:
    workflow = artifacts.load_artifact(artifact_id)
    primary_section = workflow.primary_section()

    with _state_mutator() as mutator:
        mutator.start_workflow(workflow.id.to_full_local(primary_section.id))
        _save_state(mutator.freeze())
        _state_run(mutator)

    return _state_cells()


def _validate_operation_transition(
    state: MutableState, request_id: ActionRequestId, next_operation_id: FullArtifactLocalId
) -> None:
    operation_id = state.get_action_request(request_id).operation_id

    workflow = artifacts.load_artifact(operation_id.full_artifact_id)

    operation = workflow.get_section(operation_id.local_id)
    assert operation is not None

    assert isinstance(operation.meta, OperationMeta)

    if next_operation_id.local_id not in operation.meta.allowed_transtions:
        raise NotImplementedError(f"Operation '{operation_id}' can not go to '{next_operation_id}'")


@_session_required
def complete_action_request(request_id: ActionRequestId, next_operation_id: FullArtifactLocalId) -> list[Cell]:
    with _state_mutator() as mutator:
        _validate_operation_transition(mutator, request_id, next_operation_id)
        mutator.complete_action_request(request_id, next_operation_id)
        _save_state(mutator.freeze())
        _state_run(mutator)

    return _state_cells()
