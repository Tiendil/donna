import pathlib
from typing import Annotated, NoReturn

import typer

from donna.cli.utils import output_cells
from donna.core.errors import ErrorsList
from donna.domain import errors as domain_errors
from donna.domain.artifact_ids import ArtifactId, ArtifactIdPattern, ArtifactSectionId
from donna.domain.internal_ids import ActionRequestId
from donna.machine.artifacts import ArtifactPredicate
from donna.protocol.modes import Mode


def _exit_with_errors(errors: ErrorsList) -> NoReturn:
    output_cells([error.node().info() for error in errors])
    raise typer.Exit(code=0)


def _parse_result_or_exit[T](result: T | None, errors: ErrorsList | None) -> T:
    if errors is not None:
        _exit_with_errors(errors)

    assert result is not None
    return result


def _absolute_artifact_id_or_exit(value: str) -> str:
    if not value.startswith(ArtifactId.prefix):
        _exit_with_errors([domain_errors.InvalidIdFormat(id_type=ArtifactId.__name__, value=value)])

    return value


def _absolute_artifact_section_id_or_exit(value: str) -> str:
    if not value.startswith(ArtifactId.prefix):
        _exit_with_errors([domain_errors.InvalidIdFormat(id_type=f"{ArtifactSectionId.__name__} format", value=value)])

    return value


def _absolute_artifact_pattern_or_exit(value: str) -> str:
    if value in {"*", "**"} or value.startswith("*/") or value.startswith("**/"):
        return f"{ArtifactId.prefix}{value}"

    if not value.startswith(ArtifactId.prefix):
        _exit_with_errors([domain_errors.InvalidIdPattern(id_type=ArtifactIdPattern.__name__, value=value)])

    return value


def _parse_artifact_id(value: str) -> ArtifactId:
    result = ArtifactId.parse(_absolute_artifact_id_or_exit(value))
    return _parse_result_or_exit(result.ok(), result.err())


def _parse_artifact_id_pattern(value: str) -> ArtifactIdPattern:
    result = ArtifactIdPattern.parse(_absolute_artifact_pattern_or_exit(value))
    return _parse_result_or_exit(result.ok(), result.err())


def _parse_artifact_section_id(value: str) -> ArtifactSectionId:
    result = ArtifactSectionId.parse(_absolute_artifact_section_id_or_exit(value))
    return _parse_result_or_exit(result.ok(), result.err())


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
        help="Artifact ID in absolute project-root form (e.g., '@/specs/intro.md').",
    ),
]


ArtifactIdPatternArgument = Annotated[
    ArtifactIdPattern,
    typer.Argument(
        parser=_parse_artifact_id_pattern,
        help="Artifact pattern in absolute form '@/...' or rooted wildcard form like '*/x.md' and '**/x.md'.",
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
            "Artifact section ID in absolute project-root form 'artifact:section' "
            "(e.g. '@/.donna/session/plans/artifact_id_filepaths.md:finish')."
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
