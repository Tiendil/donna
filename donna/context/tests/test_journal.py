import datetime
from typing import cast

import pytest
from pytest_mock import MockerFixture

from donna.context.context import Context
from donna.context.journal import Journal
from donna.context.tests.helpers import FakeOutputEmitter
from donna.core.result import Ok
from donna.domain.artifact_ids import ArtifactSectionId
from donna.domain.internal_ids import WorkUnitId
from donna.machine.context import ValueScope
from donna.machine.tests import make as machine_make
from donna.protocol import errors as protocol_errors
from donna.protocol import modes as protocol_modes


class _FakeStateCache:
    def __init__(self) -> None:
        self.state = machine_make.mutable_state(tasks=[machine_make.task()]).freeze()

    def load(self) -> object:
        return Ok(self.state)


class _FakeContext:
    def __init__(self) -> None:
        self.state = _FakeStateCache()
        self.current_work_unit_id: ValueScope[WorkUnitId] = ValueScope()
        self.current_operation_id: ValueScope[ArtifactSectionId] = ValueScope()
        self.output = FakeOutputEmitter()


class TestJournal:
    @pytest.mark.parametrize(
        ("mode", "actor_id"),
        [
            (protocol_modes.Mode.human, "human"),
            (protocol_modes.Mode.llm, "agent"),
            (protocol_modes.Mode.automation, "automation"),
        ],
    )
    def test_smart_actor_id__depends_on_selected_protocol(
        self, mocker: MockerFixture, mode: protocol_modes.Mode, actor_id: str
    ) -> None:
        mocker.patch("donna.context.journal.protocol_mode", return_value=mode)

        assert Journal(cast(Context, _FakeContext())).smart_actor_id() == actor_id

    def test_smart_actor_id__raises_for_unsupported_mode(self, mocker: MockerFixture) -> None:
        mocker.patch("donna.context.journal.protocol_mode", return_value="unsupported")

        with pytest.raises(protocol_errors.UnsupportedFormatterMode):
            Journal(cast(Context, _FakeContext())).smart_actor_id()

    def test_add__builds_writes_and_emits_journal_record(self, mocker: MockerFixture) -> None:
        now = datetime.datetime(2026, 5, 18, 8, 30, tzinfo=datetime.UTC)
        fake_context = _FakeContext()
        mocker.patch("donna.context.journal.protocol_mode", return_value=protocol_modes.Mode.llm)
        mocker.patch("donna.context.journal.now", return_value=now)
        write_record = mocker.patch("donna.context.journal.workspace_journal.write_record", return_value=Ok(None))

        with fake_context.current_work_unit_id.scope(machine_make.WORK_UNIT_ID):
            with fake_context.current_operation_id.scope(machine_make.PRIMARY_OPERATION_ID):
                result = Journal(cast(Context, fake_context)).add("message")

        assert result.is_ok()
        record = result.unwrap()
        assert record.timestamp == now
        assert record.actor_id == "agent"
        assert record.message == "message"
        assert record.current_task_id == machine_make.TASK_ID
        assert record.current_work_unit_id == machine_make.WORK_UNIT_ID
        assert record.current_operation_id == machine_make.PRIMARY_OPERATION_ID
        write_record.assert_called_once_with(record)
        assert fake_context.output.journal_records == [record]

    def test_add__uses_explicit_actor_id(self, mocker: MockerFixture) -> None:
        fake_context = _FakeContext()
        mocker.patch("donna.context.journal.now", return_value=datetime.datetime(2026, 5, 18, tzinfo=datetime.UTC))
        mocker.patch("donna.context.journal.workspace_journal.write_record", return_value=Ok(None))
        protocol_mode = mocker.patch("donna.context.journal.protocol_mode")

        result = Journal(cast(Context, fake_context)).add("message", actor_id="donna")

        assert result.is_ok()
        assert result.unwrap().actor_id == "donna"
        protocol_mode.assert_not_called()
