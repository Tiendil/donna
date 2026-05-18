from pytest_mock import MockerFixture

from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result
from donna.domain.artifact_ids import ArtifactId, ArtifactSectionId
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.ids import SectionId
from donna.domain.internal_ids import ActionRequestId, TaskId, WorkUnitId
from donna.domain.python_path import PythonPath
from donna.machine import errors as machine_errors
from donna.machine.action_requests import ActionRequest
from donna.machine.artifacts import Artifact, ArtifactSection
from donna.machine.changes import Change, ChangeAddActionRequest
from donna.machine.operations import OperationKind, OperationMeta
from donna.machine.state import ConsistentState, MutableState
from donna.machine.tasks import Task, WorkUnit
from donna.runtime import sessions
from donna.runtime.tests import make

ARTIFACT_ID = ArtifactId("@/workflows/runtime.donna.md")
START_SECTION_ID = SectionId("start")
NEXT_SECTION_ID = SectionId("next")
OTHER_SECTION_ID = SectionId("other")
START_OPERATION_ID = ArtifactSectionId("@/workflows/runtime.donna.md:start")
NEXT_OPERATION_ID = ArtifactSectionId("@/workflows/runtime.donna.md:next")
OTHER_OPERATION_ID = ArtifactSectionId("@/workflows/runtime.donna.md:other")
OPERATION_KIND = PythonPath(NormalizedRawIdPath("donna.runtime.tests.test_sessions.operation"))
TASK_ID = TaskId("T-1-b")
WORK_UNIT_ID = WorkUnitId("WU-2-c")
ACTION_REQUEST_ID = ActionRequestId("AR-3-d")


class _NoopOperation(OperationKind):
    def execute_section(
        self,
        task: Task,
        unit: WorkUnit,
        artifact: Artifact,
        section_id: SectionId,
    ) -> Result[list[Change], ErrorsList]:
        return Ok([])


class _RequestActionOperation(OperationKind):
    def execute_section(
        self,
        task: Task,
        unit: WorkUnit,
        artifact: Artifact,
        section_id: SectionId,
    ) -> Result[list[Change], ErrorsList]:
        request = ActionRequest.build(
            title="Choose next",
            request="Pick the next operation",
            operation_id=unit.operation_id,
        )
        return Ok([ChangeAddActionRequest(action_request=request)])


def _operation_section(
    *,
    id: SectionId,
    primary: bool = False,
    allowed_transitions: set[SectionId] | None = None,
) -> ArtifactSection:
    return ArtifactSection(
        id=id,
        artifact_id=ARTIFACT_ID,
        kind=OPERATION_KIND,
        title=f"Operation {id}",
        description=f"Description for {id}",
        primary=primary,
        meta=OperationMeta(allowed_transtions=allowed_transitions or set()),
    )


def _artifact() -> Artifact:
    return Artifact(
        id=ARTIFACT_ID,
        sections=[
            _operation_section(id=START_SECTION_ID, primary=True, allowed_transitions={NEXT_SECTION_ID}),
            _operation_section(id=NEXT_SECTION_ID),
            _operation_section(id=OTHER_SECTION_ID),
        ],
    )


def _context(
    *,
    state: ConsistentState | None = None,
    primitive: OperationKind | None = None,
) -> make.FakeRuntimeContext:
    return make.FakeRuntimeContext(
        state=state or MutableState.build().freeze(),
        artifact=_artifact(),
        primitive=primitive or _NoopOperation(),
    )


def _task() -> Task:
    return Task.build(id=TASK_ID, workflow_id=START_OPERATION_ID)


def _work_unit() -> WorkUnit:
    return WorkUnit.build(id=WORK_UNIT_ID, task_id=TASK_ID, operation_id=START_OPERATION_ID)


def _action_request(operation_id: ArtifactSectionId = START_OPERATION_ID) -> ActionRequest:
    return ActionRequest(
        id=ACTION_REQUEST_ID,
        title="Choose next",
        request="Pick next",
        operation_id=operation_id,
    )


class TestLoadState:
    def test_returns_loaded_state(self) -> None:
        state = MutableState.build().freeze()
        runtime_context = _context(state=state)

        with make.installed_context(runtime_context):
            result = sessions.load_state()

        assert result.is_ok()
        assert result.unwrap() == state
        assert runtime_context.state.saved == []

    def test_creates_empty_state_when_session_state_is_missing(self) -> None:
        runtime_context = _context()
        runtime_context.state.state = None
        runtime_context.state.errors = [machine_errors.SessionStateNotInitialized()]

        with make.installed_context(runtime_context):
            result = sessions.load_state()

        assert result.is_ok()
        loaded_state = result.unwrap()
        assert loaded_state == MutableState.build().freeze()
        assert runtime_context.state.saved == [loaded_state]

    def test_returns_non_initialization_errors_without_saving(self) -> None:
        error = machine_errors.SessionStateChangedExternally()
        runtime_context = _context()
        runtime_context.state.errors = [error]

        with make.installed_context(runtime_context):
            result = sessions.load_state()

        assert result.is_err()
        assert result.unwrap_err() == [error]
        assert runtime_context.state.saved == []


class TestNewSession:
    def test_creates_fresh_state_and_reports_success(self) -> None:
        existing_state = MutableState.build()
        existing_state.mark_started()
        runtime_context = _context(state=existing_state.freeze())

        with make.installed_context(runtime_context):
            result = sessions.new_session()

        assert result.is_ok()
        assert runtime_context.state.saved == [MutableState.build().freeze()]
        assert runtime_context.journal.records == [{"message": "Created new session state.", "actor_id": None}]
        assert result.unwrap()[0].kind == "operation_succeeded"


class TestClear:
    def test_resets_workspace_session_dir_and_reports_success(self, mocker: MockerFixture) -> None:
        reset_dir = mocker.patch("donna.runtime.sessions.workspace_sessions.reset_dir")

        result = sessions.clear()

        assert result.is_ok()
        reset_dir.assert_called_once_with()
        assert result.unwrap()[0].kind == "operation_succeeded"


class TestContinue:
    def test_runs_queued_work_until_action_request_and_returns_details(self) -> None:
        state = MutableState(
            tasks=[_task()],
            work_units=[_work_unit()],
            action_requests=[],
            started=True,
            last_id=2,
        )
        runtime_context = _context(state=state.freeze(), primitive=_RequestActionOperation())

        with make.installed_context(runtime_context):
            result = sessions.continue_()

        assert result.is_ok()
        final_state = runtime_context.state.state
        assert final_state is not None
        assert final_state.work_units == []
        assert len(final_state.action_requests) == 1
        assert runtime_context.state.saved[-1] == final_state
        assert [cell.kind for cell in result.unwrap()] == ["session_state_status", "action_request"]


class TestStatus:
    def test_returns_current_state_info_cell(self) -> None:
        runtime_context = _context()

        with make.installed_context(runtime_context):
            result = sessions.status()

        assert result.is_ok()
        assert [cell.kind for cell in result.unwrap()] == ["session_state_status"]


class TestDetails:
    def test_returns_current_state_detail_cells(self) -> None:
        state = MutableState(
            tasks=[_task()],
            work_units=[],
            action_requests=[_action_request()],
            started=True,
            last_id=3,
        )
        runtime_context = _context(state=state.freeze())

        with make.installed_context(runtime_context):
            result = sessions.details()

        assert result.is_ok()
        assert [cell.kind for cell in result.unwrap()] == ["session_state_status", "action_request"]


class TestStartWorkflow:
    def test_starts_primary_workflow_operation_runs_it_and_returns_details(self) -> None:
        runtime_context = _context(primitive=_RequestActionOperation())

        with make.installed_context(runtime_context):
            result = sessions.start_workflow(ARTIFACT_ID)

        assert result.is_ok()
        final_state = runtime_context.state.state
        assert final_state is not None
        assert final_state.started
        assert len(final_state.tasks) == 1
        assert final_state.work_units == []
        assert len(final_state.action_requests) == 1
        assert runtime_context.artifacts.loaded[0][0] == ARTIFACT_ID
        assert runtime_context.artifacts.viewed == [ARTIFACT_ID]
        assert [cell.kind for cell in result.unwrap()] == ["session_state_status", "action_request"]


class TestValidateOperationTransition:
    def test_accepts_allowed_transition(self) -> None:
        state = MutableState(
            tasks=[_task()],
            work_units=[],
            action_requests=[_action_request()],
            started=True,
            last_id=3,
        )
        runtime_context = _context()

        with make.installed_context(runtime_context):
            result = sessions._validate_operation_transition(state, ACTION_REQUEST_ID, NEXT_OPERATION_ID)

        assert result.is_ok()

    def test_rejects_disallowed_transition(self) -> None:
        state = MutableState(
            tasks=[_task()],
            work_units=[],
            action_requests=[_action_request()],
            started=True,
            last_id=3,
        )
        runtime_context = _context()

        with make.installed_context(runtime_context):
            result = sessions._validate_operation_transition(state, ACTION_REQUEST_ID, OTHER_OPERATION_ID)

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.InvalidOperationTransition)
        assert error.operation_id == START_OPERATION_ID
        assert error.next_operation_id == OTHER_OPERATION_ID


class TestCompleteActionRequest:
    def test_completes_request_runs_next_operation_and_returns_details(self) -> None:
        state = MutableState(
            tasks=[_task()],
            work_units=[],
            action_requests=[_action_request()],
            started=True,
            last_id=3,
        )
        runtime_context = _context(state=state.freeze())

        with make.installed_context(runtime_context):
            result = sessions.complete_action_request(ACTION_REQUEST_ID, NEXT_OPERATION_ID)

        assert result.is_ok()
        final_state = runtime_context.state.state
        assert final_state is not None
        assert final_state.action_requests == []
        assert final_state.work_units == []
        assert len(runtime_context.state.saved) == 2
        assert runtime_context.artifacts.executed[0][0] == ARTIFACT_ID
        assert [cell.kind for cell in result.unwrap()] == ["session_state_status"]

    def test_returns_error_for_disallowed_transition_without_saving(self) -> None:
        state = MutableState(
            tasks=[_task()],
            work_units=[],
            action_requests=[_action_request()],
            started=True,
            last_id=3,
        )
        runtime_context = _context(state=state.freeze())

        with make.installed_context(runtime_context):
            result = sessions.complete_action_request(ACTION_REQUEST_ID, OTHER_OPERATION_ID)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], machine_errors.InvalidOperationTransition)
        assert runtime_context.state.saved == []
