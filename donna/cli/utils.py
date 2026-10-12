from collections.abc import Iterable, Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

import typer
from llm_tool_cli.cli.context import CommandContext as BaseCommandContext
from llm_tool_cli.cli.handling import handle_command_errors
from llm_tool_cli.config import load_project
from llm_tool_cli.config.project import project_config
from llm_tool_cli.config.runtime import runtime_config
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import UnwrapError
from llm_tool_cli.paths import PathInput
from llm_tool_cli.protocol import write_output
from llm_tool_cli.protocol.logic_cells.base import LogicCell
from llm_tool_cli.protocol.rendering import write_cells

from donna.context.artifacts import ArtifactsCache
from donna.context.journal import Journal
from donna.context.output import output
from donna.context.primitives import PrimitivesCache
from donna.context.state import StateCache
from donna.machine import Caches, ExecutionContext
from donna.machine.caches import caches
from donna.machine.context import execution_context
from donna.machine.journal import journal
from donna.protocol.errors import environment_error_node
from donna.protocol.journal import JournalRecord
from donna.protocol.modes import get_journal_formatter
from donna.workspaces import config as workspace_config


class CliEmitter:
    __slots__ = ()

    def emit_cells(self, cells: Iterable[LogicCell], *, stderr: bool = False) -> None:
        write_cells(cells, protocol=runtime_config.get().protocol, stderr=stderr)

    def emit_journal(self, record: JournalRecord) -> None:
        formatter = get_journal_formatter(runtime_config.get().protocol)
        write_output(formatter.format_journal(record).decode("utf-8"))


class CommandContext(BaseCommandContext):
    __slots__ = ()

    def target_dir(self) -> PathInput:
        return PathInput(project_config.get().project_dir)


@contextmanager
def command_context(context: typer.Context, *, load_environment: bool = True) -> Iterator[CommandContext]:
    command = CommandContext(context)
    with output.scope(CliEmitter()), handle_command_errors(protocol=command.protocol), ExitStack() as resources:
        if load_environment:
            loaded_config = context.with_resource(
                load_project(workspace_config.Config, cwd=PathInput(Path.cwd()), path=command.config_input)
            ).unwrap()
            resources.enter_context(workspace_config.config.scope(loaded_config))
            resources.enter_context(
                caches.scope(Caches(artifacts=ArtifactsCache(), primitives=PrimitivesCache(), state=StateCache()))
            )
            resources.enter_context(execution_context.scope(ExecutionContext()))
            resources.enter_context(journal.scope(Journal()))

        try:
            yield command
        except UnwrapError as error:
            if load_environment:
                _write_errors_to_journal(error.errors)
            raise


def _write_errors_to_journal(errors: EnvironmentErrors) -> None:
    for error in errors:
        message = f"Error: {environment_error_node(error).journal_message()} [{error.code}]"

        journal.get().add(
            message=message,
            actor_id="donna",
        )
