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
CellsResult = Result[list[Cell], ErrorsList]


def _session_required(
    func: Callable[P, CellsResult],
) -> Callable[P, CellsResult]:
    # TODO: refactor to catch domain exception from load_state
    #       when we implement domain exceptions
    @functools.wraps(func)
    @unwrap_to_error
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> CellsResult:
        load_state().unwrap()
        return func(*args, **kwargs)

    return wrapper


@unwrap_to_error
def start() -> Result[list[Cell], ErrorsList]:
    world_tmp.clear()
    workspace_utils.session_world().unwrap().initialize(reset=True)

    machine_journal.reset().unwrap()

    machine_journal.add(
        message="Started new session.",
        current_task_id=None,
        current_work_unit_id=None,
        current_operation_id=None,
    ).unwrap()
    _save_state(MutableState.build().freeze()).unwrap()

    return Ok([operation_succeeded("Started new session.")])


@unwrap_to_error
def reset() -> Result[list[Cell], ErrorsList]:
    _save_state(MutableState.build().freeze()).unwrap()
    return Ok([operation_succeeded("Session state reset.")])


@unwrap_to_error
def clear() -> Result[list[Cell], ErrorsList]:
    world_tmp.clear()
    workspace_utils.session_world().unwrap().initialize(reset=True)
    return Ok([operation_succeeded("Cleared session.")])


@_session_required
@unwrap_to_error
def continue_() -> Result[list[Cell], ErrorsList]:
    mutator = load_state().unwrap().mutator()
    _state_run(mutator).unwrap()
    return _state_cells()


@_session_required
@unwrap_to_error
def status() -> Result[list[Cell], ErrorsList]:
    return Ok([load_state().unwrap().node().info()])


@_session_required
@unwrap_to_error
def details() -> Result[list[Cell], ErrorsList]:
    return Ok(load_state().unwrap().node().details())


@_session_required
@unwrap_to_error
def start_workflow(artifact_id: FullArtifactId) -> Result[list[Cell], ErrorsList]:  # noqa: CCR001
    static_state = load_state().unwrap()
    workflow = artifacts.load_artifact(artifact_id).unwrap()
    primary_section = workflow.primary_section().unwrap()
    mutator = static_state.mutator()
    mutator.start_workflow(workflow.id.to_full_local(primary_section.id)).unwrap()
    _save_state(mutator.freeze()).unwrap()
    _state_run(mutator).unwrap()
    return _state_cells()


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
@unwrap_to_error
def complete_action_request(
    request_id: ActionRequestId, next_operation_id: FullArtifactSectionId
) -> Result[list[Cell], ErrorsList]:
    mutator = load_state().unwrap().mutator()
    _validate_operation_transition(mutator, request_id, next_operation_id).unwrap()
    mutator.complete_action_request(request_id, next_operation_id).unwrap()
    _save_state(mutator.freeze()).unwrap()
    _state_run(mutator).unwrap()
    return _state_cells()
