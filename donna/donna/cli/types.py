from typing import Annotated

import typer

from donna.cli.utils import output_cells
from donna.core.errors import ErrorsList
from donna.domain.ids import ActionRequestId, FullArtifactId, FullArtifactIdPattern, FullArtifactSectionId


def _exit_with_errors(errors: ErrorsList) -> None:
    output_cells([error.node().info() for error in errors])
    raise typer.Exit(code=0)


def _parse_full_artifact_id(value: str) -> FullArtifactId:
    result = FullArtifactId.parse(value)
    errors = result.err()
    if errors is not None:
        _exit_with_errors(errors)

    return result.unwrap()


def _parse_full_artifact_id_pattern(value: str) -> FullArtifactIdPattern:
    result = FullArtifactIdPattern.parse(value)
    errors = result.err()
    if errors is not None:
        _exit_with_errors(errors)

    return result.unwrap()


def _parse_full_artifact_section_id(value: str) -> FullArtifactSectionId:
    result = FullArtifactSectionId.parse(value)
    errors = result.err()
    if errors is not None:
        _exit_with_errors(errors)

    return result.unwrap()


ActionRequestIdArgument = Annotated[
    ActionRequestId,
    typer.Argument(parser=ActionRequestId, help="The ID of the action request"),
]


FullArtifactIdArgument = Annotated[
    FullArtifactId,
    typer.Argument(parser=_parse_full_artifact_id, help="The full ID of the artifact"),
]


FullArtifactIdPatternOption = Annotated[
    FullArtifactIdPattern | None,
    typer.Option(parser=_parse_full_artifact_id_pattern, help="The full artifact pattern to list"),
]


FullArtifactSectionIdArgument = Annotated[
    FullArtifactSectionId,
    typer.Argument(parser=_parse_full_artifact_section_id, help="The full section ID of the artifact"),
]
