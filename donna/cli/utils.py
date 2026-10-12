from collections.abc import Iterable, Iterator
from contextlib import ExitStack, contextmanager
from contextvars import Token
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
from donna.context.context import Context
from donna.context.primitives import PrimitivesCache
from donna.context.state import StateCache
from donna.machine import Caches, ExecutionContext
from donna.machine.caches import caches
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


def output_cells(cells: Iterable[LogicCell]) -> None:
    CliEmitter().emit_cells(cells)


class CommandContext(BaseCommandContext):
    __slots__ = ("emitter",)

    def __init__(self, context: typer.Context) -> None:
        super().__init__(context)
        self.emitter = CliEmitter()

    def target_dir(self) -> PathInput:
        return PathInput(project_config.get().project_dir)


@contextmanager
def command_context(context: typer.Context, *, load_environment: bool = True) -> Iterator[CommandContext]:
    from donna.context import reset_context, set_context
    from donna.machine import context as machine_context

    command = CommandContext(context)
    context_token: Token[Context | None] | None = None
    machine_context_token: Token[machine_context.MachineContext | None] | None = None

    try:
        with handle_command_errors(protocol=command.protocol), ExitStack() as resources:
            try:
                if load_environment:
                    loaded_config = context.with_resource(
                        load_project(workspace_config.Config, cwd=PathInput(Path.cwd()), path=command.config_input)
                    ).unwrap()
                    resources.enter_context(workspace_config.config.scope(loaded_config))
                    resources.enter_context(
                        caches.scope(
                            Caches(artifacts=ArtifactsCache(), primitives=PrimitivesCache(), state=StateCache())
                        )
                    )
                    resources.enter_context(machine_context.execution_context.scope(ExecutionContext()))
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
