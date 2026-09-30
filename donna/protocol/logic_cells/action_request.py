import textwrap

from llm_tool_cli.protocol.logic_cells.uniform import UniformCell
from llm_tool_cli.protocol.output_cells.base import OutputCell

from donna.domain.internal_ids import ActionRequestId


class ActionRequestCell(UniformCell):
    action_request_id: ActionRequestId | None
    request: str

    def _render(self, cell_type: type[OutputCell]) -> OutputCell:
        message = textwrap.dedent(
            """
        **This is an action request for the agent. You MUST follow the instructions below.**

        {request}
        """
        ).format(request=self.request)

        return cell_type.build_markdown(
            kind="action_request",
            content=message,
            action_request_id=str(self.action_request_id),
        )
