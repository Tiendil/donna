import json
import subprocess  # noqa: S404

import pytest
from llm_tool_cli.core.settings import ToolLabel
from llm_tool_cli.output.journal import CommandJournalProcessor
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.output_cells.base import RenderContext
from pytest_mock import MockerFixture

from donna.protocol.tests.make import journal_record


class TestJournalCell:
    @pytest.mark.parametrize(
        ("protocol", "expected"),
        [
            (Protocol.human, "10:30:45 [42] <agent> Completed step\n"),
            (
                Protocol.llm,
                "2026-05-18T10:30:45+00:00 [task-42-Q] <agent> [work-unit-7-h] "
                "[@/workflow.donna.md:operation] Completed step\n",
            ),
        ],
    )
    def test_render__preserves_compact_context(self, protocol: Protocol, expected: str) -> None:
        context = RenderContext(index=0, total=1, tool_label=ToolLabel("TEST"))
        assert journal_record().render(protocol)[0].render(context).decode() == expected

    @pytest.mark.parametrize("protocol", list(Protocol))
    def test_render__multiline_message_is_preserved_and_displayed_on_one_line(self, protocol: Protocol) -> None:
        cell = journal_record(message="  line\nnext\rfinal  ")
        context = RenderContext(index=0, total=1, tool_label=ToolLabel("TEST"))
        text = cell.render(protocol)[0].render(context).decode()
        assert len(text.splitlines()) == 1
        if protocol == Protocol.automation:
            record = json.loads(text)
            assert record == cell.model_dump(mode="json")
            assert record["message"] == "line\nnext\rfinal"
        else:
            assert r"line\nnext\rfinal" in text

    def test_render__missing_context_uses_placeholders(self) -> None:
        cell = journal_record(
            actor_id=None, current_task_id=None, current_work_unit_id=None, current_operation_id=None
        )
        context = RenderContext(index=0, total=1, tool_label=ToolLabel("TEST"))
        assert cell.render(Protocol.human)[0].render(context).decode() == "10:30:45 [-] <-> Completed step\n"
        assert (
            cell.render(Protocol.llm)[0].render(context).decode()
            == "2026-05-18T10:30:45+00:00 [-] <-> [-] [-] Completed step\n"
        )

    def test_render__automation_keeps_existing_fields(self) -> None:
        context = RenderContext(index=0, total=1, tool_label=ToolLabel("TEST"))
        record = json.loads(journal_record().render(Protocol.automation)[0].render(context))
        assert record == {
            "timestamp": "2026-05-18T10:30:45Z",
            "actor_id": "agent",
            "message": "Completed step",
            "current_task_id": "task-42-Q",
            "current_work_unit_id": "work-unit-7-h",
            "current_operation_id": "@/workflow.donna.md:operation",
        }

    def test_forwarding__shared_processor_uses_domain_fields(self, mocker: MockerFixture) -> None:
        run = mocker.patch(
            "llm_tool_cli.output.journal.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", "")
        )
        processor = CommandJournalProcessor(
            [
                "tool",
                "{timestamp}",
                "{current_task_id}",
                "{current_work_unit_id}",
                "{current_operation_id}",
                "{message}",
            ]
        )
        processor.process(journal_record(message="  first\nsecond\n  ").to_journal_record()).unwrap()
        run.assert_called_once_with(
            [
                "tool",
                "2026-05-18T10:30:45+00:00",
                "task-42-Q",
                "work-unit-7-h",
                "@/workflow.donna.md:operation",
                "first\nsecond",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
