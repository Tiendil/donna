import textwrap

from llm_tool_cli.protocol.logic_cells.uniform import UniformCell
from llm_tool_cli.protocol.output_cells.base import OutputCell


class SessionStateCell(UniformCell):
    started: bool
    tasks: int
    queued_work_units: int
    pending_action_requests: int

    def _render(self, cell_type: type[OutputCell]) -> OutputCell:
        if not self.started:
            message = textwrap.dedent(
                """
            This is a new session; no tasks were performed. You can safely run a workflow.
                """
            )

        elif not self.tasks:
            message = textwrap.dedent(
                """
            The session is IDLE. There are no active tasks.

            - If the developer asked you to start working on a new task, you can do so by running a new workflow.
            - If you have been working on a task, consider it completed and REPORT THE RESULTS TO THE DEVELOPER.
                """
            )

        elif self.queued_work_units:
            message = textwrap.dedent(
                """
            The session has PENDING WORK UNITS. Donna has work to complete.

            - If the developer asked you to start working on a new task, you MUST warn that there are pending work
              units and ask if you should start a new session or continue working on the current work units.
            - If you have been working on a task, you can continue session.
                """
            )

        elif self.pending_action_requests:
            message = textwrap.dedent(
                """
            The session is AWAITING YOUR ACTION. You have pending action requests to address.

            - If the developer asked you to start working on a new task, you MUST ask if you should start a new session
              or continue working on the current action requests.
            - Otherwise, you MUST address the pending action requests before proceeding.
                """
            )

        else:
            message = textwrap.dedent(
                """
            The session has unfinished TASKS but no pending work units or action requests.

            - If the developer asked you to start working on a new task , you MUST ask if you should start a new
              session or run a new workflow in the current one.
            - If you have been working on a task, you can consider it completed and output the results to the
              developer.
                """
            )

        return cell_type.build_markdown(
            kind="session_state_status",
            content=message,
            tasks=self.tasks,
            queued_work_units=self.queued_work_units,
            pending_action_requests=self.pending_action_requests,
        )
