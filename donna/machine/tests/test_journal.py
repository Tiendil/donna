import pytest
from llm_tool_cli.config.runtime import RuntimeConfig, runtime_config
from llm_tool_cli.core.errors import EnvironmentError
from llm_tool_cli.core.result import Err
from llm_tool_cli.output import output
from llm_tool_cli.protocol import Protocol
from pytest_mock import MockerFixture

from donna.context.tests.helpers import FakeOutputEmitter
from donna.domain.internal_ids import TaskId
from donna.machine import Caches, ExecutionContext
from donna.machine.caches import caches
from donna.machine.context import execution_context
from donna.machine.errors import SessionStateChangedExternally, SessionStateNotInitialized
from donna.machine.journal import journal_cell
from donna.machine.tests import make
from donna.machine.tests.helpers import FakeArtifacts, FakePrimitives
from donna.runtime.tests.make import FakeStateStore


class TestJournalCell:
    @pytest.mark.parametrize(
        ("protocol", "actor"),
        [(Protocol.human, "human"), (Protocol.llm, "agent"), (Protocol.automation, "automation")],
    )
    @pytest.mark.parametrize("has_task", [False, True])
    def test_derives_context(self, protocol: Protocol, actor: str, has_task: bool) -> None:
        state = FakeStateStore(state=make.mutable_state(tasks=[make.task()] if has_task else []).freeze())
        emitter = FakeOutputEmitter()
        context = ExecutionContext(
            current_work_unit_id=make.WORK_UNIT_ID, current_operation_id=make.PRIMARY_OPERATION_ID
        )
        with (
            caches.scope(Caches(artifacts=FakeArtifacts(), primitives=FakePrimitives(), state=state)),
            execution_context.scope(context),
            runtime_config.scope(RuntimeConfig(protocol=protocol)),
            output.scope(emitter),
        ):
            output.get().journal("event").unwrap()

        assert state.loaded_count == 1
        assert not state.saved
        assert [cell.model_dump(exclude={"timestamp"}) for cell in emitter.journal_records] == [
            {
                "message": "event",
                "actor_id": actor,
                "current_task_id": make.TASK_ID if has_task else None,
                "current_work_unit_id": make.WORK_UNIT_ID,
                "current_operation_id": make.PRIMARY_OPERATION_ID,
            }
        ]

    @pytest.mark.parametrize("actor", [None, "donna"])
    def test_explicit_actor_retains_task_and_execution_context(self, actor: str | None) -> None:
        state = FakeStateStore(state=make.mutable_state(tasks=[make.task()]).freeze())
        emitter = FakeOutputEmitter()
        context = ExecutionContext(
            current_work_unit_id=make.WORK_UNIT_ID, current_operation_id=make.PRIMARY_OPERATION_ID
        )
        with (
            caches.scope(Caches(artifacts=FakeArtifacts(), primitives=FakePrimitives(), state=state)),
            execution_context.scope(context),
            output.scope(emitter),
        ):
            output.get().journal("event", actor_id=actor).unwrap()

        assert state.loaded_count == 1
        assert [cell.model_dump(exclude={"timestamp"}) for cell in emitter.journal_records] == [
            {
                "message": "event",
                "actor_id": actor,
                "current_task_id": make.TASK_ID,
                "current_work_unit_id": make.WORK_UNIT_ID,
                "current_operation_id": make.PRIMARY_OPERATION_ID,
            }
        ]

    @pytest.mark.parametrize("has_parent", [False, True])
    def test_task_changes_only_after_saving_mutable_state(self, has_parent: bool) -> None:
        parent = make.task()
        child = make.task(id=TaskId("T-2-c"))
        tasks = [parent, child] if has_parent else [child]
        snapshot = make.mutable_state(tasks=tasks).freeze()
        state = FakeStateStore(state=snapshot)
        mutator = snapshot.mutator()
        mutator.remove_task(child.id)
        emitter = FakeOutputEmitter()
        context = ExecutionContext(current_work_unit_id=make.WORK_UNIT_ID)
        with (
            caches.scope(Caches(artifacts=FakeArtifacts(), primitives=FakePrimitives(), state=state)),
            execution_context.scope(context),
            output.scope(emitter),
        ):
            output.get().journal("Before saving", actor_id="donna").unwrap()
            state.save(mutator.freeze()).unwrap()
            output.get().journal("After saving", actor_id="donna").unwrap()

        assert [record.current_task_id for record in emitter.journal_records] == [
            child.id,
            parent.id if has_parent else None,
        ]
        assert all(record.current_work_unit_id == make.WORK_UNIT_ID for record in emitter.journal_records)
        assert all(record.current_operation_id is None for record in emitter.journal_records)

    @pytest.mark.parametrize("error", [SessionStateNotInitialized(), SessionStateChangedExternally()])
    @pytest.mark.parametrize("has_execution", [False, True])
    def test_unavailable_session_emits_without_task(self, error: EnvironmentError, has_execution: bool) -> None:
        state = FakeStateStore(errors=[error])
        emitter = FakeOutputEmitter()
        context = ExecutionContext(
            current_work_unit_id=make.WORK_UNIT_ID if has_execution else None,
            current_operation_id=make.PRIMARY_OPERATION_ID if has_execution else None,
        )
        with (
            caches.scope(Caches(artifacts=FakeArtifacts(), primitives=FakePrimitives(), state=state)),
            execution_context.scope(context),
            runtime_config.scope(RuntimeConfig(protocol=Protocol.llm)),
            output.scope(emitter),
        ):
            result = output.get().journal("event")

        assert result.is_ok()
        assert state.loaded_count == 1
        assert not state.saved
        assert [cell.model_dump(exclude={"timestamp"}) for cell in emitter.journal_records] == [
            {
                "message": "event",
                "actor_id": "agent",
                "current_task_id": None,
                "current_work_unit_id": make.WORK_UNIT_ID if has_execution else None,
                "current_operation_id": make.PRIMARY_OPERATION_ID if has_execution else None,
            }
        ]

    @pytest.mark.parametrize("with_session", [False, True])
    def test_emitter_failure_propagates(self, mocker: MockerFixture, with_session: bool) -> None:
        failure = EnvironmentError(code="forward_failed", message="Forwarding failed")
        state = FakeStateStore(
            state=make.mutable_state().freeze(), errors=None if with_session else [SessionStateNotInitialized()]
        )
        emitter = FakeOutputEmitter()
        emit = mocker.patch.object(emitter, "emit", return_value=Err([failure]))
        with (
            caches.scope(Caches(artifacts=FakeArtifacts(), primitives=FakePrimitives(), state=state)),
            execution_context.scope(ExecutionContext()),
            output.scope(emitter),
        ):
            result = output.get().journal("event", actor_id="donna")

        assert result.unwrap_err() == [failure]
        emit.assert_called_once()

    def test_unexpected_session_failure_propagates(self, mocker: MockerFixture) -> None:
        state = FakeStateStore()
        mocker.patch.object(state, "load", side_effect=ValueError("unexpected defect"))
        with caches.scope(Caches(artifacts=FakeArtifacts(), primitives=FakePrimitives(), state=state)):
            with pytest.raises(ValueError, match="unexpected defect"):
                journal_cell(message="event", actor_id=None)
