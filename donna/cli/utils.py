import pathlib
import sys
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import Token

import typer
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.config import load_config, locate_config
from llm_tool_cli.core import errors as llm_tool_errors
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Ok, Result, UnwrapError, unwrap_to_error

from donna.cli.entities import GLOBAL_OPTIONS_CONTEXT_KEY, GlobalOptions
from donna.context.context import Context
from donna.core.errors import EnvironmentError
from donna.domain.constants import DONNA_CONFIG_NAME
from donna.domain.paths import PathInput, ProjectConfigPath, UntrustedPath
from donna.protocol.cells import Cell
from donna.protocol.errors import environment_error_node
from donna.protocol.formatters import Formatter
from donna.protocol.journal import JournalRecord
from donna.protocol.modes import Mode, get_cell_formatter
from donna.workspaces import config as workspace_config


def instant_output(text: bytes, *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    if text.endswith(b"\n"):
        stream.buffer.write(text)
    else:
        stream.buffer.write(text + b"\n")
    stream.buffer.flush()


class CliEmitter:
    __slots__ = ("_formatter",)

    def __init__(self, formatter: Formatter) -> None:
        self._formatter = formatter

    def emit_cell(self, cell: Cell) -> None:
        instant_output(self._formatter.format_cell(cell))

    def emit_journal(self, record: JournalRecord) -> None:
        instant_output(self._formatter.format_journal(record))

    def emit_error(self, error: llm_tool_errors.EnvironmentError, *, stderr: bool) -> None:
        instant_output(self._formatter.format_error(error), error=stderr)


def output_cells(cells: Iterable[Cell]) -> None:
    emitter = CliEmitter(get_cell_formatter(workspace_config.protocol()))

    for cell in cells:
        emitter.emit_cell(cell)


def global_options(context: typer.Context) -> GlobalOptions:
    global_options = context.find_root().meta.get(GLOBAL_OPTIONS_CONTEXT_KEY)

    if isinstance(global_options, GlobalOptions):
        return global_options

    return GlobalOptions(protocol=Mode.human)


class CommandContext:
    __slots__ = ("emitter", "global_options", "protocol")

    def __init__(self, context: typer.Context) -> None:
        self.global_options = global_options(context)
        self.protocol = self.global_options.protocol
        self.emitter = CliEmitter(get_cell_formatter(self.protocol))

    def install_protocol(self) -> None:
        if not workspace_config.protocol.is_set():
            workspace_config.protocol.set(self.protocol)

    @unwrap_to_error
    def load_workspace(self) -> Result[workspace_config.Workspace, EnvironmentErrors]:
        config_path = ProjectConfigPath(
            locate_config(DONNA_CONFIG_NAME, path=self.global_options.config_path, cwd=pathlib.Path.cwd()).unwrap()
        )
        loaded_config = load_config(config_path, workspace_config.Config).unwrap()
        workspace = workspace_config.construct_workspace(loaded_config, config_path=config_path)
        workspace_config.install_workspace(workspace)
        return Ok(workspace)

    def target_config_path(self) -> ProjectConfigPath:
        if self.global_options.config_path is not None:
            return ProjectConfigPath(self.global_options.config_path)

        return ProjectConfigPath(pathlib.Path.cwd() / DONNA_CONFIG_NAME)

    def target_dir(self) -> PathInput:
        if workspace_config.project_dir.is_set():
            return workspace_config.project_dir()

        if self.global_options.config_path is not None:
            return UntrustedPath(pathlib.Path(self.global_options.config_path).parent)

        return UntrustedPath(pathlib.Path.cwd())

    def write_cells(self, cells: Iterable[Cell]) -> None:
        for cell in cells:
            self.emitter.emit_cell(cell)

    def write_errors(self, errors: EnvironmentErrors) -> int:
        exit_code = 0
        for error in errors:
            if isinstance(error, EnvironmentError):
                self.emitter.emit_cell(environment_error_node(error).info())
            else:
                self.emitter.emit_error(error, stderr=self.protocol != Mode.automation)
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
        errors = _errors_from_unwrap(error)
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


def _errors_from_unwrap(error: UnwrapError) -> EnvironmentErrors:
    unwrapped = error.details["error"]

    if isinstance(unwrapped, llm_tool_errors.EnvironmentError):
        return [unwrapped]

    if isinstance(unwrapped, Iterable):
        items = list(unwrapped)
        errors = [item for item in items if isinstance(item, llm_tool_errors.EnvironmentError)]
        if len(errors) == len(items):
            return errors

    raise error
