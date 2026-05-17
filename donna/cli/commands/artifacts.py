import sys
from typing import Annotated

import click
import typer

from donna.cli.application import app
from donna.cli.types import ArtifactIdArgument, ArtifactIdsArgument, RenderModeOption, parse_artifact_id_argument
from donna.cli.utils import command_context
from donna.context.context import context
from donna.machine import journal as machine_journal
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.errors import environment_error_node
from donna.workspaces.artifacts import RENDER_CONTEXT_VIEW, ArtifactRenderContext, fetch_artifact_bytes
from donna.workspaces.templates import render as render_template


def _log_artifact_operation(message: str) -> None:
    machine_journal.add(message=message)


@app.command(name="list", help="List available workflow artifacts and show their status summaries.")
def list_(
    typer_context: typer.Context,
) -> None:
    with command_context(typer_context) as command:
        _log_artifact_operation("List artifacts")

        artifacts = context().artifacts.list(RENDER_CONTEXT_VIEW).unwrap()

        command.write_cells(artifact.node().status() for artifact in artifacts)


@app.command(help="Render an artifact with the selected render mode and write the markdown to stdout.")
def render(
    typer_context: typer.Context,
    artifact_path: ArtifactIdArgument,
    mode: RenderModeOption,
) -> None:
    with command_context(typer_context) as command:
        artifact_id = parse_artifact_id_argument(artifact_path, command.target_dir())
        _log_artifact_operation(f"Render artifact `{artifact_id}` in `{mode.value}` mode")

        content = fetch_artifact_bytes(artifact_id).unwrap().decode("utf-8")
        render_context = ArtifactRenderContext(primary_mode=mode)
        rendered = render_template(artifact_id, content, render_context).unwrap()

        sys.stdout.write(rendered)


@app.command(help="Validate the given artifact ids, or validate every discovered artifact with --all.")
def validate(  # noqa: CCR001
    typer_context: typer.Context,
    artifact_paths: ArtifactIdsArgument = None,
    all_artifacts: Annotated[
        bool,
        typer.Option("--all", help="Validate every discovered artifact."),
    ] = False,
) -> None:
    with command_context(typer_context) as command:
        if all_artifacts and artifact_paths:
            raise click.UsageError("Pass artifact ids or --all, not both.")

        if not all_artifacts and not artifact_paths:
            raise click.UsageError("Pass artifact ids or --all.")

        if all_artifacts:
            _log_artifact_operation("Validate all artifacts")
            artifacts = context().artifacts.list(RENDER_CONTEXT_VIEW).unwrap()
        else:
            assert artifact_paths is not None
            artifact_ids = [
                parse_artifact_id_argument(artifact_path, command.target_dir()) for artifact_path in artifact_paths
            ]
            _log_artifact_operation(
                f"Validate artifacts {', '.join(f'`{artifact_id}`' for artifact_id in artifact_ids)}"
            )
            artifacts = [
                context().artifacts.load(artifact_id, RENDER_CONTEXT_VIEW).unwrap() for artifact_id in artifact_ids
            ]

        errors = []

        for artifact in artifacts:
            result = artifact.validate_artifact()
            if result.is_err():
                errors.extend(result.unwrap_err())

        if errors:
            command.write_cells(environment_error_node(error).info() for error in errors)
            return

        command.write_cells([operation_succeeded("All artifacts are valid")])
