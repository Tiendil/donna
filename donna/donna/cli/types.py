from typing import Annotated

import typer

from donna.domain.ids import ActionRequestId, FullArtifactId, FullArtifactIdPattern, FullArtifactSectionId


def _parse_full_artifact_id(value: str) -> FullArtifactId:
    result = FullArtifactId.parse(value)
    errors = result.err()
    if errors is not None:
        error = errors[0]
        raise typer.BadParameter(error.message.format(error=error))

    parsed = result.ok()
    if parsed is None:
        raise typer.BadParameter(f"Invalid {FullArtifactId.__name__}: {value!r}")

    return parsed


def _parse_full_artifact_id_pattern(value: str) -> FullArtifactIdPattern:
    result = FullArtifactIdPattern.parse(value)
    errors = result.err()
    if errors is not None:
        error = errors[0]
        raise typer.BadParameter(error.message.format(error=error))

    parsed = result.ok()
    if parsed is None:
        raise typer.BadParameter(f"Invalid {FullArtifactIdPattern.__name__}: {value!r}")

    return parsed


def _parse_full_artifact_section_id(value: str) -> FullArtifactSectionId:
    result = FullArtifactSectionId.parse(value)
    errors = result.err()
    if errors is not None:
        error = errors[0]
        raise typer.BadParameter(error.message.format(error=error))

    parsed = result.ok()
    if parsed is None:
        raise typer.BadParameter(f"Invalid {FullArtifactSectionId.__name__}: {value!r}")

    return parsed


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
