from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

import typer
from llm_tool_cli.cli.context import CommandContext as BaseCommandContext
from llm_tool_cli.cli.handling import handle_command_errors
from llm_tool_cli.config import load_project
from llm_tool_cli.config.project import project_config
from llm_tool_cli.core.result import UnwrapError
from llm_tool_cli.output import StreamOutputEmitter, output
from llm_tool_cli.output.errors import EnvironmentError as OutputEnvironmentError
from llm_tool_cli.output.journal import CommandJournalProcessor
from llm_tool_cli.paths import PathInput

from donna.context.artifacts import ArtifactsCache
from donna.context.primitives import PrimitivesCache
from donna.context.state import StateCache
from donna.machine import Caches, ExecutionContext
from donna.machine.caches import caches
from donna.machine.context import execution_context
from donna.machine.journal import journal_emit
from donna.workspaces import config as workspace_config


class CommandContext(BaseCommandContext):
    __slots__ = ()

    def target_dir(self) -> PathInput:
        return PathInput(project_config.get().project_dir)


@contextmanager
def command_context(  # noqa: CCR001
    context: typer.Context, *, load_environment: bool = True
) -> Iterator[CommandContext]:
    command = CommandContext(context)
    with handle_command_errors(protocol=command.protocol), ExitStack() as resources:
        if load_environment:
            loaded_config = context.with_resource(
                load_project(workspace_config.Config, cwd=PathInput(Path.cwd()), path=command.config_input)
            ).unwrap()
            resources.enter_context(workspace_config.config.scope(loaded_config))
            if loaded_config.journal.cmd is not None:
                context.with_resource(
                    output.scope(
                        StreamOutputEmitter(journal_processor=CommandJournalProcessor(loaded_config.journal.cmd))
                    )
                )
            resources.enter_context(
                caches.scope(Caches(artifacts=ArtifactsCache(), primitives=PrimitivesCache(), state=StateCache()))
            )
            resources.enter_context(execution_context.scope(ExecutionContext()))

        try:
            yield command
        except UnwrapError as error:
            if load_environment:
                for failure in error.errors:
                    if isinstance(failure, OutputEnvironmentError):
                        continue
                    message = failure.format_message().replace("\n", " ").strip()
                    journal_emit(f"Error: {message} [{failure.code}]", actor_id="donna")
            raise
