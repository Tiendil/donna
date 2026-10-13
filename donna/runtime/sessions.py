import functools
from typing import Callable, ParamSpec

from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error
from llm_tool_cli.output import output
from llm_tool_cli.protocol.cell_shortcuts import operation_succeeded

from donna.domain.artifact_ids import ArtifactId, ArtifactSectionId, artifact_section_id, split_artifact_section_id
from donna.domain.internal_ids import ActionRequestId
from donna.machine import errors as machine_errors
from donna.machine.caches import caches
from donna.machine.operations import OperationMeta
from donna.machine.state import ConsistentState, MutableState
from donna.machine.templates import RENDER_CONTEXT_VIEW
from donna.workspaces import sessions as workspace_sessions


@unwrap_to_error
def load_state() -> Result[ConsistentState]:
    loaded = caches.get().state.load()

    if loaded.is_ok():
        return Ok(loaded.unwrap())

    errors = loaded.unwrap_err()
    if not any(isinstance(error, machine_errors.SessionStateNotInitialized) for error in errors):
        return Err(errors)

    state = MutableState.build().freeze()
    caches.get().state.save(state).unwrap()
    return Ok(state)


@unwrap_to_error
def _save_state(state: ConsistentState) -> Result[None]:
    caches.get().state.save(state).unwrap()
    return Ok(None)


@unwrap_to_error
def _state_run(mutator: MutableState) -> Result[None]:
    while mutator.has_work():
        mutator.execute_next_work_unit().unwrap()
        _save_state(mutator.freeze()).unwrap()

    return Ok(None)


@unwrap_to_error
def _emit_state() -> Result[None]:
    return output.get().emit(load_state().unwrap().details_cells())


P = ParamSpec("P")


def _session_required(
    func: Callable[P, Result[None]],
) -> Callable[P, Result[None]]:
    # TODO: refactor to catch domain exception from load_state
    #       when we implement domain exceptions
    @functools.wraps(func)
    @unwrap_to_error
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[None]:
        load_state().unwrap()
        return func(*args, **kwargs)

    return wrapper


@unwrap_to_error
def new_session() -> Result[None]:
    _save_state(MutableState.build().freeze()).unwrap()

    output.get().journal("Created new session state.").unwrap()

    return output.get().emit([operation_succeeded("Created new session state.")])


@unwrap_to_error
def clear() -> Result[None]:
    workspace_sessions.reset_dir()
    return output.get().emit([operation_succeeded("Cleared session.")])


@_session_required
@unwrap_to_error
def continue_() -> Result[None]:
    mutator = load_state().unwrap().mutator()
    _state_run(mutator).unwrap()
    return _emit_state()


@_session_required
@unwrap_to_error
def status() -> Result[None]:
    return output.get().emit([load_state().unwrap().status_cell()])


@_session_required
@unwrap_to_error
def details() -> Result[None]:
    return _emit_state()


@_session_required
@unwrap_to_error
def start_workflow(artifact_id: ArtifactId) -> Result[None]:  # noqa: CCR001
    static_state = load_state().unwrap()
    workflow = caches.get().artifacts.load(artifact_id, RENDER_CONTEXT_VIEW).unwrap()
    primary_section = workflow.primary_section().unwrap()
    mutator = static_state.mutator()
    mutator.start_workflow(artifact_section_id(workflow.id, primary_section.id)).unwrap()
    _save_state(mutator.freeze()).unwrap()
    _state_run(mutator).unwrap()
    return _emit_state()


@unwrap_to_error
def _validate_operation_transition(
    state: MutableState, request_id: ActionRequestId, next_operation_id: ArtifactSectionId
) -> Result[None]:
    operation_id = state.get_action_request(request_id).unwrap().operation_id
    operation_parts = split_artifact_section_id(operation_id)
    assert operation_parts is not None
    next_operation_parts = split_artifact_section_id(next_operation_id)
    assert next_operation_parts is not None

    workflow = caches.get().artifacts.load(operation_parts.artifact_id, RENDER_CONTEXT_VIEW).unwrap()
    operation = workflow.get_section(operation_parts.section_id).unwrap()

    assert isinstance(operation.meta, OperationMeta)

    if next_operation_parts.section_id not in operation.meta.allowed_transitions:
        return Err(
            [machine_errors.InvalidOperationTransition(operation_id=operation_id, next_operation_id=next_operation_id)]
        )

    return Ok(None)


@_session_required
@unwrap_to_error
def complete_action_request(request_id: ActionRequestId, next_operation_id: ArtifactSectionId) -> Result[None]:
    mutator = load_state().unwrap().mutator()
    _validate_operation_transition(mutator, request_id, next_operation_id).unwrap()
    mutator.complete_action_request(request_id, next_operation_id).unwrap()
    _save_state(mutator.freeze()).unwrap()
    _state_run(mutator).unwrap()
    return _emit_state()
