from typing import Annotated

import click
import typer

from donna.cli.application import app
from donna.cli.types import ArtifactIdsArgument
from donna.cli.utils import command_context
from donna.context.context import context
from donna.machine import journal as machine_journal
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.workspaces.artifacts import RENDER_CONTEXT_VIEW

artifacts_cli = typer.Typer()


def _log_artifact_operation(message: str) -> None:
    machine_journal.add(message=message)


@artifacts_cli.command(name="list", help="List available workflow artifacts and show their status summaries.")
def list_(
    typer_context: typer.Context,
) -> None:
    with command_context(typer_context) as command:
        _log_artifact_operation("List artifacts")

        artifacts = context().artifacts.list(RENDER_CONTEXT_VIEW).unwrap()

        command.write_cells(artifact.node().status() for artifact in artifacts)


@artifacts_cli.command(help="Validate the given artifact ids, or validate every discovered artifact with --all.")
def validate(  # noqa: CCR001
    typer_context: typer.Context,
    artifact_ids: ArtifactIdsArgument = None,
    all_artifacts: Annotated[
        bool,
        typer.Option("--all", help="Validate every discovered artifact."),
    ] = False,
) -> None:
    with command_context(typer_context) as command:
        if all_artifacts and artifact_ids:
            raise click.UsageError("Pass artifact ids or --all, not both.")

        if not all_artifacts and not artifact_ids:
            raise click.UsageError("Pass artifact ids or --all.")

        if all_artifacts:
            _log_artifact_operation("Validate all artifacts")
            artifacts = context().artifacts.list(RENDER_CONTEXT_VIEW).unwrap()
        else:
            assert artifact_ids is not None
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
            command.write_cells(error.node().info() for error in errors)
            return

        command.write_cells([operation_succeeded("All artifacts are valid")])


app.add_typer(
    artifacts_cli,
    name="artifacts",
    help="Inspect and validate stored artifacts in the Donna project.",
)
