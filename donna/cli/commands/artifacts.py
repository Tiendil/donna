from typing import Annotated

import click
import typer
from llm_tool_cli.core.result import Err
from llm_tool_cli.output import output
from llm_tool_cli.protocol.cell_shortcuts import operation_succeeded
from llm_tool_cli.protocol.logic_cells import ContentCell

from donna.cli.application import app
from donna.cli.types import ArtifactIdArgument, ArtifactIdsArgument, RenderModeOption, parse_artifact_id_argument
from donna.cli.utils import command_context
from donna.machine import ArtifactRenderContext
from donna.machine.caches import caches
from donna.machine.journal import journal_emit
from donna.machine.templates import RENDER_CONTEXT_VIEW
from donna.workspaces.artifacts import fetch_artifact_bytes
from donna.workspaces.templates import render as render_template


@app.command(name="list", help="List available workflow artifacts and show their status summaries.")
def list_(
    typer_context: typer.Context,
) -> None:
    with command_context(typer_context):
        journal_emit("List artifacts").unwrap()

        artifacts = caches.get().artifacts.list(RENDER_CONTEXT_VIEW).unwrap()

        output.get().emit([artifact.status_cell() for artifact in artifacts]).unwrap()


@app.command(help="Render an artifact with the selected render mode and output a Markdown cell.")
def render(
    typer_context: typer.Context,
    artifact_path: ArtifactIdArgument,
    mode: RenderModeOption,
) -> None:
    with command_context(typer_context) as command:
        artifact_id = parse_artifact_id_argument(artifact_path, command.target_dir()).unwrap()
        journal_emit(f"Render artifact `{artifact_id}` in `{mode.value}` mode").unwrap()

        content = fetch_artifact_bytes(artifact_id).unwrap().decode("utf-8")
        render_context = ArtifactRenderContext(primary_mode=mode)
        rendered = render_template(artifact_id, content, render_context).unwrap()

        output.get().emit(
            [
                ContentCell(
                    kind="rendered_artifact",
                    media_type="text/markdown",
                    content=rendered,
                    meta={"type": "rendered_artifact"},
                )
            ]
        ).unwrap()


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
            journal_emit("Validate all artifacts").unwrap()
            artifacts = caches.get().artifacts.list(RENDER_CONTEXT_VIEW).unwrap()
        else:
            assert artifact_paths is not None
            artifact_ids = [
                parse_artifact_id_argument(artifact_path, command.target_dir()).unwrap()
                for artifact_path in artifact_paths
            ]
            journal_emit(
                f"Validate artifacts {', '.join(f'`{artifact_id}`' for artifact_id in artifact_ids)}"
            ).unwrap()
            artifacts = [
                caches.get().artifacts.load(artifact_id, RENDER_CONTEXT_VIEW).unwrap() for artifact_id in artifact_ids
            ]

        errors = []

        for artifact in artifacts:
            result = artifact.validate_artifact()
            if result.is_err():
                errors.extend(result.unwrap_err())

        if errors:
            Err(errors).unwrap()

        output.get().emit([operation_succeeded("All artifacts are valid")]).unwrap()
