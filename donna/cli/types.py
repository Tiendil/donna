import pathlib
from typing import Annotated

import typer

from donna.cli.utils import output_cells
from donna.core.errors import ErrorsList
from donna.domain.artifact_ids import ArtifactId, ArtifactIdPattern, ArtifactSectionId
from donna.domain.internal_ids import ActionRequestId
from donna.machine.artifacts import ArtifactPredicate
from donna.protocol.modes import Mode


def _exit_with_errors(errors: ErrorsList) -> None:
    output_cells([error.node().info() for error in errors])
    raise typer.Exit(code=0)


def _parse_artifact_id(value: str) -> ArtifactId:
    result = ArtifactId.parse(value)
    errors = result.err()
    if errors is not None:
        _exit_with_errors(errors)

    return result.unwrap()


def _parse_artifact_id_pattern(value: str) -> ArtifactIdPattern:
    result = ArtifactIdPattern.parse(value)
    errors = result.err()
    if errors is not None:
        _exit_with_errors(errors)

    return result.unwrap()


def _parse_artifact_section_id(value: str) -> ArtifactSectionId:
    result = ArtifactSectionId.parse(value)
    errors = result.err()
    if errors is not None:
        _exit_with_errors(errors)

    return result.unwrap()


def _parse_artifact_predicate(value: str) -> ArtifactPredicate:
    result = ArtifactPredicate.parse(value)
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


def _parse_input_path(value: str) -> pathlib.Path:
    normalized = value.strip()
    if normalized == "-":
        return pathlib.Path("-")

    path = pathlib.Path(normalized).expanduser()
    if not path.exists():
        raise typer.BadParameter(f"Input path '{value}' does not exist.")
    if not path.is_file():
        raise typer.BadParameter(f"Input path '{value}' is not a file.")

    if not path.is_absolute():
        path = path.resolve()

    return path


ActionRequestIdArgument = Annotated[
    ActionRequestId,
    typer.Argument(
        parser=_parse_action_request_id,
        help="Action request ID (for example: AR-12-x).",
    ),
]


ArtifactIdArgument = Annotated[
    ArtifactId,
    typer.Argument(
        parser=_parse_artifact_id,
        help="Artifact ID in project-relative form 'artifact[:path]' (e.g., 'specs:intro').",
    ),
]


ArtifactIdPatternArgument = Annotated[
    ArtifactIdPattern,
    typer.Argument(
        parser=_parse_artifact_id_pattern,
        help="Artifact pattern (supports '*' and '**', e.g. 'specs:*' or '**:intro').",
    ),
]

PredicateOption = Annotated[
    ArtifactPredicate | None,
    typer.Option(
        "--predicate",
        "-p",
        parser=_parse_artifact_predicate,
        help="Filter artifacts by predicate expression evaluated with `section` global.",
    ),
]


ArtifactSectionIdArgument = Annotated[
    ArtifactSectionId,
    typer.Argument(
        parser=_parse_artifact_section_id,
        help=(
            "Artifact section ID in project-relative form 'artifact:section' "
            "(e.g. '.donna:session:execute_rfc:finish')."
        ),
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

SpecsOption = Annotated[
    bool,
    typer.Option(
        "--specs/--no-specs",
        help="Enable or disable Donna specs updates in `.agents/donna`.",
    ),
]


InputPathArgument = Annotated[
    pathlib.Path,
    typer.Argument(
        parser=_parse_input_path,
        help="Path to an existing local file used as input, or '-' to read from stdin.",
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
