import functools
from typing import Callable, ParamSpec

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import ActionRequestId, FullArtifactId, FullArtifactSectionId, WorldId
from donna.machine import errors as machine_errors
from donna.machine.operations import OperationMeta
from donna.machine.state import ConsistentState, MutableState
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.cells import Cell
from donna.world import artifacts
from donna.world import tmp as world_tmp
from donna.world.config import config
from donna.world.worlds.base import World


def _errors_to_cells(errors: ErrorsList) -> list[Cell]:
    return [error.node().info() for error in errors]


def _session() -> Result[World, ErrorsList]:
    world_result = config().get_world(WorldId("session"))
    if world_result.is_err():
        return Err(world_result.unwrap_err())

    world = world_result.unwrap()

    if not world.is_initialized():
        world.initialize(reset=False)

    return Ok(world)


def _load_state() -> Result[ConsistentState, ErrorsList]:
    session_result = _session()
    if session_result.is_err():
        return Err(session_result.unwrap_err())

    content = session_result.unwrap().read_state("state.json")

    if content is None:
        return Err([machine_errors.SessionStateNotInitialized()])

    return Ok(ConsistentState.from_json(content.decode("utf-8")))


def _save_state(state: ConsistentState) -> Result[None, ErrorsList]:
    session_result = _session()
    if session_result.is_err():
        return Err(session_result.unwrap_err())

    session_result.unwrap().write_state("state.json", state.to_json().encode("utf-8"))
    return Ok(None)


def _state_run(mutator: MutableState) -> Result[None, ErrorsList]:
    while mutator.has_work():
        execution_result = mutator.exectute_next_work_unit()
        if execution_result.is_err():
            return Err(execution_result.unwrap_err())

        save_result = _save_state(mutator.freeze())
        if save_result.is_err():
            return Err(save_result.unwrap_err())

    return Ok(None)


def _state_cells() -> Result[list[Cell], ErrorsList]:
    state_result = _load_state()
    if state_result.is_err():
        return Err(state_result.unwrap_err())

    return Ok(state_result.unwrap().node().details())


P = ParamSpec("P")


def _session_required(func: Callable[P, list[Cell]]) -> Callable[P, list[Cell]]:
    # TODO: refactor to catch domain exception from load_state
    #       when we implement domain exceptions
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[Cell]:
        state_result = _load_state()
        if state_result.is_err():
            return _errors_to_cells(state_result.unwrap_err())

        return func(*args, **kwargs)

    return wrapper


def start() -> list[Cell]:
    world_tmp.clear()
    session_result = _session()
    if session_result.is_err():
        return _errors_to_cells(session_result.unwrap_err())

    session_result.unwrap().initialize(reset=True)

    save_result = _save_state(MutableState.build().freeze())
    if save_result.is_err():
        return _errors_to_cells(save_result.unwrap_err())

    return [operation_succeeded("Started new session.")]


def clear() -> list[Cell]:
    world_tmp.clear()
    session_result = _session()
    if session_result.is_err():
        return _errors_to_cells(session_result.unwrap_err())

    session_result.unwrap().initialize(reset=True)
    return [operation_succeeded("Cleared session.")]


@_session_required
def continue_() -> list[Cell]:
    state_result = _load_state()
    if state_result.is_err():
        return _errors_to_cells(state_result.unwrap_err())

    mutator = state_result.unwrap().mutator()
    run_result = _state_run(mutator)
    if run_result.is_err():
        return _errors_to_cells(run_result.unwrap_err())

    cells_result = _state_cells()
    if cells_result.is_err():
        return _errors_to_cells(cells_result.unwrap_err())

    return cells_result.unwrap()


@_session_required
def status() -> list[Cell]:
    state_result = _load_state()
    if state_result.is_err():
        return _errors_to_cells(state_result.unwrap_err())

    return [state_result.unwrap().node().info()]


@_session_required
def start_workflow(artifact_id: FullArtifactId) -> list[Cell]:
    workflow_result = artifacts.load_artifact(artifact_id)
    if workflow_result.is_err():
        return _errors_to_cells(workflow_result.unwrap_err())

    workflow = workflow_result.unwrap()
    primary_section = workflow.primary_section()

    state_result = _load_state()
    if state_result.is_err():
        return _errors_to_cells(state_result.unwrap_err())

    mutator = state_result.unwrap().mutator()
    mutator.start_workflow(workflow.id.to_full_local(primary_section.id))
    save_result = _save_state(mutator.freeze())
    if save_result.is_err():
        return _errors_to_cells(save_result.unwrap_err())

    run_result = _state_run(mutator)
    if run_result.is_err():
        return _errors_to_cells(run_result.unwrap_err())

    cells_result = _state_cells()
    if cells_result.is_err():
        return _errors_to_cells(cells_result.unwrap_err())

    return cells_result.unwrap()


def _validate_operation_transition(
    state: MutableState, request_id: ActionRequestId, next_operation_id: FullArtifactSectionId
) -> Result[None, ErrorsList]:
    operation_id = state.get_action_request(request_id).operation_id

    workflow_result = artifacts.load_artifact(operation_id.full_artifact_id)
    if workflow_result.is_err():
        return Err(workflow_result.unwrap_err())

    workflow = workflow_result.unwrap()

    operation = workflow.get_section(operation_id.local_id)
    assert operation is not None

    assert isinstance(operation.meta, OperationMeta)

    if next_operation_id.local_id not in operation.meta.allowed_transtions:
        raise NotImplementedError(f"Operation '{operation_id}' can not go to '{next_operation_id}'")

    return Ok(None)


@_session_required
def complete_action_request(request_id: ActionRequestId, next_operation_id: FullArtifactSectionId) -> list[Cell]:
    state_result = _load_state()
    if state_result.is_err():
        return _errors_to_cells(state_result.unwrap_err())

    mutator = state_result.unwrap().mutator()
    transition_result = _validate_operation_transition(mutator, request_id, next_operation_id)
    if transition_result.is_err():
        return _errors_to_cells(transition_result.unwrap_err())

    mutator.complete_action_request(request_id, next_operation_id)
    save_result = _save_state(mutator.freeze())
    if save_result.is_err():
        return _errors_to_cells(save_result.unwrap_err())

    run_result = _state_run(mutator)
    if run_result.is_err():
        return _errors_to_cells(run_result.unwrap_err())

    cells_result = _state_cells()
    if cells_result.is_err():
        return _errors_to_cells(cells_result.unwrap_err())

    return cells_result.unwrap()
