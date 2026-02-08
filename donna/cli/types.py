import pathlib
from typing import Annotated

import typer

from donna.cli.utils import output_cells
from donna.core.errors import ErrorsList
from donna.domain.ids import ActionRequestId, FullArtifactId, FullArtifactIdPattern, FullArtifactSectionId
from donna.protocol.modes import Mode


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


def _parse_action_request_id(value: str) -> ActionRequestId:
    if not ActionRequestId.validate(value):
        raise typer.BadParameter("Invalid action request ID format (expected '<prefix>-<number>-<crc>').")
    return ActionRequestId(value)


def _parse_protocol_mode(value: str) -> Mode:
    try:
        return Mode(value)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in Mode)
        raise typer.BadParameter(f"Unsupported protocol mode '{value}'. Expected one of: {allowed}.") from exc


ActionRequestIdArgument = Annotated[
    ActionRequestId,
    typer.Argument(
        parser=_parse_action_request_id,
        help="Action request ID (for example: AR-12-x).",
    ),
]


FullArtifactIdArgument = Annotated[
    FullArtifactId,
    typer.Argument(
        parser=_parse_full_artifact_id,
        help="Full artifact ID in the form 'world:artifact[:path]' (e.g., 'project:intro').",
    ),
]


FullArtifactIdPatternArgument = Annotated[
    FullArtifactIdPattern,
    typer.Argument(
        parser=_parse_full_artifact_id_pattern,
        help="Artifact pattern (supports '*' and '**', e.g. 'project:*' or '**:intro').",
    ),
]

TagOption = Annotated[
    list[str] | None,
    typer.Option(
        "--tag",
        help="Filter artifacts by tag. Repeatable.",
    ),
]


FullArtifactSectionIdArgument = Annotated[
    FullArtifactSectionId,
    typer.Argument(
        parser=_parse_full_artifact_section_id,
        help="Full artifact section ID in the form 'world:artifact:section'.",
    ),
]


ProtocolModeOption = Annotated[
    Mode,
    typer.Option(
        "--protocol",
        "-p",
        parser=_parse_protocol_mode,
        help="Protocol mode to use (required). Examples: --protocol=llm, -p llm.",
    ),
]


RootOption = Annotated[
    pathlib.Path | None,
    typer.Option(
        "--root",
        "-r",
        resolve_path=True,
        file_okay=False,
        dir_okay=True,
        exists=True,
        help=(
            "Optional project root directory. "
            "If omitted, Donna discovers it by searching parent directories for the workspace."
        ),
    ),
]

SkillsOption = Annotated[
    bool,
    typer.Option(
        "--skills/--no-skills",
        help="Enable or disable skills updates in `.agents/skills`.",
    ),
]


InputPathArgument = Annotated[
    pathlib.Path,
    typer.Argument(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Path to an existing local file used as input.",
    ),
]


OutputPathOption = Annotated[
    pathlib.Path | None,
    typer.Option(
        resolve_path=True,
        dir_okay=False,
        file_okay=True,
        help="Optional output file path (file only). Defaults to a temporary file if omitted.",
    ),
]

ProjectDirArgument = Annotated[
    pathlib.Path | None,
    typer.Argument(
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Optional project directory. Defaults to the current working directory.",
    ),
]
