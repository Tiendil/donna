import typer

from donna.cli.application import app
from donna.cli.types import ArtifactIdPatternArgument, PredicateOption, validate_supported_artifact_pattern
from donna.cli.utils import command_context
from donna.context.context import context
from donna.domain.artifact_ids import ArtifactIdPattern
from donna.machine import journal as machine_journal
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.workspaces.artifacts import RENDER_CONTEXT_VIEW

artifacts_cli = typer.Typer()

DEFAULT_ARTIFACT_PATTERN = ArtifactIdPattern.parse("**").unwrap()


def _log_artifact_operation(message: str) -> None:
    machine_journal.add(message=message)


def _log_operation_on_artifacts(
    message: str,
    pattern: ArtifactIdPattern,
    predicate: PredicateOption | None,
) -> None:
    if predicate is None:
        return _log_artifact_operation(f"{message} `{pattern}`")

    return _log_artifact_operation(f"{message} `{pattern}` with predicate `{predicate.source}`")


@artifacts_cli.command(help="List available workflow artifacts and show their status summaries.")
def list(
    typer_context: typer.Context,
) -> None:
    with command_context(typer_context) as command:
        _log_artifact_operation("List artifacts")

        artifacts = context().artifacts.list(DEFAULT_ARTIFACT_PATTERN, RENDER_CONTEXT_VIEW).unwrap()

        command.write_cells(artifact.node().status() for artifact in artifacts)


@artifacts_cli.command(
    help=(
        "Validate artifacts matching a pattern with the Donna artifact extension "
        "(defaults to all artifacts) and return any errors."
    )
)
def validate(
    typer_context: typer.Context,
    pattern: ArtifactIdPatternArgument = DEFAULT_ARTIFACT_PATTERN,
    predicate: PredicateOption = None,
) -> None:  # noqa: CCR001
    with command_context(typer_context) as command:
        validate_supported_artifact_pattern(pattern)
        _log_operation_on_artifacts("Validate artifacts", pattern, predicate)

        artifacts = context().artifacts.list(pattern, RENDER_CONTEXT_VIEW, predicate=predicate).unwrap()

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
