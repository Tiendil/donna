import functools
from typing import Callable, ParamSpec

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import ActionRequestId, FullArtifactId, FullArtifactSectionId
from donna.machine import errors as machine_errors
from donna.machine import journal as machine_journal
from donna.machine.operations import OperationMeta
from donna.machine.state import ConsistentState, MutableState
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.cells import Cell
from donna.workspaces import artifacts
from donna.workspaces import tmp as world_tmp
from donna.workspaces import utils as workspace_utils


def _errors_to_cells(errors: ErrorsList) -> list[Cell]:
    return [error.node().info() for error in errors]


@unwrap_to_error
def load_state() -> Result[ConsistentState, ErrorsList]:
    content = workspace_utils.session_world().unwrap().read_state("state.json").unwrap()
    if content is None:
        return Err([machine_errors.SessionStateNotInitialized()])

    return Ok(ConsistentState.from_json(content.decode("utf-8")))


@unwrap_to_error
def _save_state(state: ConsistentState) -> Result[None, ErrorsList]:
    workspace_utils.session_world().unwrap().write_state("state.json", state.to_json().encode("utf-8")).unwrap()
    return Ok(None)


@unwrap_to_error
def _state_run(mutator: MutableState) -> Result[None, ErrorsList]:
    while mutator.has_work():
        mutator.execute_next_work_unit().unwrap()
        _save_state(mutator.freeze()).unwrap()

    return Ok(None)


@unwrap_to_error
def _state_cells() -> Result[list[Cell], ErrorsList]:
    return Ok(load_state().unwrap().node().details())


P = ParamSpec("P")


def _session_required(func: Callable[P, list[Cell]]) -> Callable[P, list[Cell]]:
    # TODO: refactor to catch domain exception from load_state
    #       when we implement domain exceptions
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[Cell]:
        state_result = load_state()
        if state_result.is_err():
            return _errors_to_cells(state_result.unwrap_err())

        return func(*args, **kwargs)

    return wrapper


def start() -> list[Cell]:
    world_tmp.clear()
    session_result = workspace_utils.session_world()
    if session_result.is_err():
        return _errors_to_cells(session_result.unwrap_err())

    session_result.unwrap().initialize(reset=True)

    reset_journal_result = machine_journal.reset()
    if reset_journal_result.is_err():
        return _errors_to_cells(reset_journal_result.unwrap_err())

    journal_message_result = machine_journal.add(
        message="Started new session.",
        current_task_id=None,
        current_work_unit_id=None,
        current_operation_id=None,
    )
    if journal_message_result.is_err():
        return _errors_to_cells(journal_message_result.unwrap_err())

    save_result = _save_state(MutableState.build().freeze())
    if save_result.is_err():
        return _errors_to_cells(save_result.unwrap_err())

    return [operation_succeeded("Started new session.")]


def reset() -> list[Cell]:
    save_result = _save_state(MutableState.build().freeze())
    if save_result.is_err():
        return _errors_to_cells(save_result.unwrap_err())

    return [operation_succeeded("Session state reset.")]


def clear() -> list[Cell]:
    world_tmp.clear()
    session_result = workspace_utils.session_world()
    if session_result.is_err():
        return _errors_to_cells(session_result.unwrap_err())

    session_result.unwrap().initialize(reset=True)
    return [operation_succeeded("Cleared session.")]


@_session_required
def continue_() -> list[Cell]:
    state_result = load_state()
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
    state_result = load_state()
    if state_result.is_err():
        return _errors_to_cells(state_result.unwrap_err())

    return [state_result.unwrap().node().info()]


@_session_required
def details() -> list[Cell]:
    state_result = load_state()
    if state_result.is_err():
        return _errors_to_cells(state_result.unwrap_err())

    return state_result.unwrap().node().details()


@_session_required
def start_workflow(artifact_id: FullArtifactId) -> list[Cell]:  # noqa: CCR001
    state_result = load_state()
    if state_result.is_err():
        return _errors_to_cells(state_result.unwrap_err())

    static_state = state_result.unwrap()

    machine_journal.add(
        message=f"Start workflow `{artifact_id}`",
        current_task_id=str(static_state.current_task.id) if static_state.current_task else None,
        current_work_unit_id=None,
        current_operation_id=None,
    ).unwrap()

    workflow_result = artifacts.load_artifact(artifact_id)
    if workflow_result.is_err():
        return _errors_to_cells(workflow_result.unwrap_err())

    workflow = workflow_result.unwrap()
    primary_section_result = workflow.primary_section()
    if primary_section_result.is_err():
        return _errors_to_cells(primary_section_result.unwrap_err())

    primary_section = primary_section_result.unwrap()

    state_result = load_state()
    if state_result.is_err():
        return _errors_to_cells(state_result.unwrap_err())

    mutator = static_state.mutator()
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


@unwrap_to_error
def _validate_operation_transition(
    state: MutableState, request_id: ActionRequestId, next_operation_id: FullArtifactSectionId
) -> Result[None, ErrorsList]:
    operation_id = state.get_action_request(request_id).unwrap().operation_id
    workflow = artifacts.load_artifact(operation_id.full_artifact_id).unwrap()
    operation = workflow.get_section(operation_id.local_id).unwrap()

    assert isinstance(operation.meta, OperationMeta)

    if next_operation_id.local_id not in operation.meta.allowed_transtions:
        return Err(
            [machine_errors.InvalidOperationTransition(operation_id=operation_id, next_operation_id=next_operation_id)]
        )

    return Ok(None)


@_session_required
def complete_action_request(request_id: ActionRequestId, next_operation_id: FullArtifactSectionId) -> list[Cell]:
    state_result = load_state()
    if state_result.is_err():
        return _errors_to_cells(state_result.unwrap_err())

    static_state = state_result.unwrap()

    machine_journal.add(
        message=f"Complete action request `{request_id}`, transit to `{next_operation_id}`",
        current_task_id=str(static_state.current_task.id) if static_state.current_task else None,
        current_work_unit_id=None,
        current_operation_id=None,
    ).unwrap()

    mutator = static_state.mutator()
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
