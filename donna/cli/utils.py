from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

import typer
from llm_tool_cli.cli.context import command_context as shared_command_context
from llm_tool_cli.config import load_project
from llm_tool_cli.output import StreamOutputEmitter, output
from llm_tool_cli.paths import PathInput

from donna.context.artifacts import ArtifactsCache
from donna.context.primitives import PrimitivesCache
from donna.context.state import StateCache
from donna.machine import Caches, ExecutionContext
from donna.machine.caches import caches
from donna.machine.context import execution_context
from donna.machine.journal import journal_cell
from donna.workspaces import config as workspace_config


@contextmanager
def command_context(context: typer.Context) -> Iterator[None]:
    with shared_command_context(context) as command, ExitStack() as resources:
        loaded_config = context.with_resource(
            load_project(workspace_config.Config, cwd=PathInput(Path.cwd()), path=command.config_input)
        ).unwrap()
        resources.enter_context(workspace_config.config.scope(loaded_config))
        resources.enter_context(
            caches.scope(Caches(artifacts=ArtifactsCache(), primitives=PrimitivesCache(), state=StateCache()))
        )
        resources.enter_context(execution_context.scope(ExecutionContext()))
        context.with_resource(
            output.scope(
                StreamOutputEmitter(journal_processor=loaded_config.journal.processor(), journal_factory=journal_cell)
            )
        )
        yield
