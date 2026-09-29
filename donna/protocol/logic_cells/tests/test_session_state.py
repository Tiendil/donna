import pytest
from llm_tool_cli.protocol import Protocol

from donna.protocol import SessionStateCell
from donna.protocol.logic_cells.tests.helpers import project


class TestSessionStateCell:
    @pytest.mark.parametrize("protocol", list(Protocol))
    @pytest.mark.parametrize(
        ("counts", "message"),
        [
            ((False, 0, 0, 0), "new session"),
            ((False, 1, 1, 1), "new session"),
            ((True, 0, 1, 1), "IDLE"),
            ((True, 1, 1, 1), "PENDING WORK UNITS"),
            ((True, 1, 0, 1), "AWAITING YOUR ACTION"),
            ((True, 1, 0, 0), "unfinished TASKS"),
        ],
    )
    def test_render__selects_status_and_preserves_counts(
        self, protocol: Protocol, counts: tuple[bool, int, int, int], message: str
    ) -> None:
        started, tasks, units, requests = counts
        cell = SessionStateCell(
            started=started, tasks=tasks, queued_work_units=units, pending_action_requests=requests
        )

        output = project(cell, protocol)

        assert output.kind == "session_state_status"
        assert output.media_type == "text/markdown"
        assert output.content is not None
        assert message in output.content
        assert output.meta == {"tasks": tasks, "queued_work_units": units, "pending_action_requests": requests}
