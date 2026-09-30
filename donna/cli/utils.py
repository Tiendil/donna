import pathlib
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import Token

import typer
from llm_tool_cli.cli.entities import GlobalOptions
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.config import load_config, locate_config
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Ok, Result, UnwrapError, unwrap_to_error
from llm_tool_cli.paths import PathInput, ProjectConfigPath
from llm_tool_cli.protocol import Protocol, write_output
from llm_tool_cli.protocol.cell_shortcuts import environment_error
from llm_tool_cli.protocol.logic_cells.base import LogicCell
from llm_tool_cli.protocol.rendering import write_cells

from donna.cli.application import GLOBAL_OPTIONS_CONTEXT_KEY
from donna.context.context import Context
from donna.core.errors import EnvironmentError
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
        write_cells(cells, protocol=self._protocol, tool_label="DONNA", stderr=stderr)

    def emit_journal(self, record: JournalRecord) -> None:
        write_output(self._journal_formatter.format_journal(record).decode("utf-8"))


def output_cells(cells: Iterable[LogicCell]) -> None:
    emitter = CliEmitter(workspace_config.protocol())

    emitter.emit_cells(cells)


def global_options(context: typer.Context) -> GlobalOptions:
    global_options = context.find_root().meta.get(GLOBAL_OPTIONS_CONTEXT_KEY)

    if isinstance(global_options, GlobalOptions):
        return global_options

    return GlobalOptions()


class CommandContext:
    __slots__ = ("emitter", "global_options", "protocol")

    def __init__(self, context: typer.Context) -> None:
        self.global_options = global_options(context)
        self.protocol = self.global_options.protocol_for(context.info_name or "")
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

    def target_config_path(self) -> ProjectConfigPath:
        if self.global_options.config_path is not None:
            return self.global_options.config_path

        return ProjectConfigPath(pathlib.Path.cwd() / DONNA_CONFIG_NAME)

    def target_dir(self) -> PathInput:
        if workspace_config.project_dir.is_set():
            return PathInput(workspace_config.project_dir())

        if self.global_options.config_path is not None:
            return PathInput(self.global_options.config_path.parent)

        return PathInput(pathlib.Path.cwd())

    def write_cells(self, cells: Iterable[LogicCell]) -> None:
        self.emitter.emit_cells(cells)

    def write_errors(self, errors: EnvironmentErrors) -> int:
        exit_code = 0
        for error in errors:
            local_error = isinstance(error, EnvironmentError)
            self.emitter.emit_cells(
                [environment_error(error)], stderr=not local_error and self.protocol != Protocol.automation
            )
            if not local_error:
                exit_code = max(exit_code, 2 if isinstance(error, config_errors.EnvironmentError) else 3)
        return exit_code


@contextmanager
def command_context(context: typer.Context, *, load_environment: bool = True) -> Iterator[CommandContext]:
    from donna.context import reset_context, set_context
    from donna.machine import context as machine_context

    command = CommandContext(context)
    context_token: Token[Context | None] | None = None
    machine_context_token: Token[machine_context.MachineContext | None] | None = None

    try:
        command.install_protocol()

        if load_environment:
            command.load_workspace().unwrap()
            runtime_context = Context(output=command.emitter)
            context_token = set_context(runtime_context)
            machine_context_token = machine_context.set_context(runtime_context)

        yield command
    except UnwrapError as error:
        errors = error.errors
        if context_token is not None:
            _write_errors_to_journal(errors)
        raise typer.Exit(code=command.write_errors(errors)) from error
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
