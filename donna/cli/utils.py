import pathlib
import sys
from collections.abc import Iterable, Iterator
from contextlib import contextmanager

import typer

from donna.cli.entities import GLOBAL_OPTIONS_CONTEXT_KEY, GlobalOptions
from donna.core.errors import EnvironmentError, ErrorsList
from donna.core.result import UnwrapError
from donna.domain.constants import DONNA_CONFIG_NAME
from donna.domain.paths import PathInput, ProjectConfigPath, UntrustedPath
from donna.protocol.cells import Cell
from donna.protocol.errors import environment_error_node
from donna.protocol.formatters.base import Formatter
from donna.protocol.journal import JournalRecord
from donna.protocol.modes import Mode, get_cell_formatter
from donna.workspaces import config as workspace_config
from donna.workspaces.initialization import load_workspace


def instant_output(text: bytes) -> None:
    if text.endswith(b"\n"):
        sys.stdout.buffer.write(text)
    else:
        sys.stdout.buffer.write(text + b"\n")
    sys.stdout.buffer.flush()


class CliEmitter:
    __slots__ = ("_formatter",)

    def __init__(self, formatter: Formatter) -> None:
        self._formatter = formatter

    def emit_cell(self, cell: Cell) -> None:
        instant_output(self._formatter.format_cell(cell))

    def emit_journal(self, record: JournalRecord) -> None:
        instant_output(self._formatter.format_journal(record))


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

    def load_workspace(self) -> workspace_config.Workspace:
        workspace = load_workspace(config_path=self.global_options.config_path).unwrap()
        workspace_config.install_workspace(workspace)
        return workspace

    def target_config_path(self) -> ProjectConfigPath:
        if self.global_options.config_path is not None:
            return ProjectConfigPath(self.global_options.config_path)

        return ProjectConfigPath(pathlib.Path.cwd() / DONNA_CONFIG_NAME)

    def target_dir(self) -> PathInput:
        if self.global_options.config_path is not None:
            return UntrustedPath(pathlib.Path(self.global_options.config_path).parent)

        if workspace_config.project_dir.is_set():
            return workspace_config.project_dir()

        return UntrustedPath(pathlib.Path.cwd())

    def write_cells(self, cells: Iterable[Cell]) -> None:
        for cell in cells:
            self.emitter.emit_cell(cell)


@contextmanager
def command_context(context: typer.Context, *, load_environment: bool = True) -> Iterator[CommandContext]:
    from donna.context import Context, set_context

    command = CommandContext(context)

    try:
        command.install_protocol()

        if load_environment:
            command.load_workspace()
            set_context(Context(output=command.emitter))

        yield command
    except UnwrapError as error:
        command.write_cells(_cells_from_unwrap(error))
        raise typer.Exit(code=0) from error


def _write_errors_to_journal(errors: ErrorsList) -> None:
    from donna.machine import journal as machine_journal

    for error in errors:
        message = f"Error: {environment_error_node(error).journal_message()} [{error.code}]"

        machine_journal.add(
            message=message,
            actor_id="donna",
        )


def _errors_from_unwrap(error: UnwrapError) -> ErrorsList:
    unwrapped = error.arguments["error"]

    if isinstance(unwrapped, EnvironmentError):
        return [unwrapped]

    if isinstance(unwrapped, Iterable):
        return [item for item in unwrapped if isinstance(item, EnvironmentError)]

    raise error


def _cells_from_unwrap(error: UnwrapError) -> Iterable[Cell]:
    errors = _errors_from_unwrap(error)

    if workspace_config.config.is_set():
        _write_errors_to_journal(errors)

    return [environment_error_node(item).info() for item in errors]
