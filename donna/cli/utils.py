import pathlib
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import Token

import typer
from llm_tool_cli.cli.context import CommandContext as BaseCommandContext
from llm_tool_cli.cli.handling import handle_command_errors
from llm_tool_cli.config import load_config, locate_config
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Ok, Result, UnwrapError, unwrap_to_error
from llm_tool_cli.paths import PathInput
from llm_tool_cli.protocol import Protocol, write_output
from llm_tool_cli.protocol.logic_cells.base import LogicCell
from llm_tool_cli.protocol.rendering import write_cells

from donna.context.context import Context
from donna.domain.constants import DONNA_CONFIG_NAME
from donna.protocol.errors import environment_error_node
from donna.protocol.journal import JournalRecord
from donna.protocol.modes import get_journal_formatter
from donna.workspaces import config as workspace_config


class CliEmitter:
    __slots__ = ("_protocol", "_journal_formatter")

    def __init__(self, protocol: Protocol) -> None:
        self._protocol = protocol

        self._journal_formatter = get_journal_formatter(protocol)

    def emit_cells(self, cells: Iterable[LogicCell], *, stderr: bool = False) -> None:
        write_cells(cells, protocol=self._protocol, stderr=stderr)

    def emit_journal(self, record: JournalRecord) -> None:
        write_output(self._journal_formatter.format_journal(record).decode("utf-8"))


def output_cells(cells: Iterable[LogicCell]) -> None:
    emitter = CliEmitter(workspace_config.protocol())

    emitter.emit_cells(cells)


class CommandContext(BaseCommandContext):
    __slots__ = ("emitter",)

    def __init__(self, context: typer.Context) -> None:
        super().__init__(context)
        self.emitter = CliEmitter(self.protocol)

    def install_protocol(self) -> None:
        if not workspace_config.protocol.is_set():
            workspace_config.protocol.set(self.protocol)

    @unwrap_to_error
    def load_workspace(self) -> Result[workspace_config.Workspace]:
        config_path = locate_config(
            DONNA_CONFIG_NAME, path=self.global_options.config_path, cwd=pathlib.Path.cwd()
        ).unwrap()
        loaded_config = load_config(config_path, workspace_config.Config).unwrap()
        workspace = workspace_config.construct_workspace(loaded_config, config_path=config_path)
        workspace_config.install_workspace(workspace)
        return Ok(workspace)

    def target_dir(self) -> PathInput:
        if workspace_config.project_dir.is_set():
            return PathInput(workspace_config.project_dir())

        if self.global_options.config_path is not None:
            return PathInput(self.global_options.config_path.parent)

        return PathInput(pathlib.Path.cwd())


@contextmanager
def command_context(context: typer.Context, *, load_environment: bool = True) -> Iterator[CommandContext]:
    from donna.context import reset_context, set_context
    from donna.machine import context as machine_context

    command = CommandContext(context)
    context_token: Token[Context | None] | None = None
    machine_context_token: Token[machine_context.MachineContext | None] | None = None

    try:
        with handle_command_errors(protocol=command.protocol):
            try:
                command.install_protocol()

                if load_environment:
                    command.load_workspace().unwrap()
                    runtime_context = Context(output=command.emitter)
                    context_token = set_context(runtime_context)
                    machine_context_token = machine_context.set_context(runtime_context)

                yield command
            except UnwrapError as error:
                if context_token is not None:
                    _write_errors_to_journal(error.errors)
                raise
    finally:
        if machine_context_token is not None:
            machine_context.reset_context(machine_context_token)

        if context_token is not None:
            reset_context(context_token)


def _write_errors_to_journal(errors: EnvironmentErrors) -> None:
    from donna.context.context import context

    for error in errors:
        message = f"Error: {environment_error_node(error).journal_message()} [{error.code}]"

        context().journal.add(
            message=message,
            actor_id="donna",
        )
