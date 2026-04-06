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
from donna.workspaces.config import config as workspace_config


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


def _match_supported_extension(filename: str) -> str | None:
    supported_extensions = workspace_config().supported_extensions()
    normalized = filename.strip().lower()

    for extension in sorted(supported_extensions, key=len, reverse=True):
        if normalized.endswith(extension):
            return extension

    return None


def _artifact_filename(value: str) -> str:
    return pathlib.PurePosixPath(value.split(ArtifactSectionId.delimiter, maxsplit=1)[0]).name


def _pattern_filename(value: str) -> str | None:
    last_part = pathlib.PurePosixPath(value).name
    if last_part in {"*", "**"}:
        return None

    dot_index = last_part.find(".")
    if dot_index == -1:
        return None

    return f"placeholder{last_part[dot_index:]}"


def validate_supported_artifact_id(artifact_id: ArtifactId) -> None:
    if _match_supported_extension(_artifact_filename(str(artifact_id))) is None:
        raise typer.BadParameter(
            f"Unsupported artifact extension for '{artifact_id}'. Use a filename extension supported by the sources."
        )


def validate_supported_artifact_pattern(pattern: ArtifactIdPattern) -> None:
    filename = _pattern_filename(str(pattern))
    if filename is None:
        return

    if _match_supported_extension(filename) is None:
        raise typer.BadParameter(
            f"Unsupported artifact extension for '{pattern}'. Use a filename extension supported by the sources."
        )


def validate_supported_artifact_section_id(section_id: ArtifactSectionId) -> None:
    validate_supported_artifact_id(section_id.artifact_id)


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
        help=(
            "Artifact ID in absolute project-root form with a supported source "
            "extension (e.g., '@/specs/intro.donna.md')."
        ),
    ),
]


ArtifactIdPatternArgument = Annotated[
    ArtifactIdPattern,
    typer.Argument(
        parser=_parse_artifact_id_pattern,
        help=(
            "Artifact pattern in absolute form '@/...' or rooted wildcard form like "
            "'*/x.donna.md' and '**/x.donna.md'. Patterns that name a file "
            "extension must use a supported source extension."
        ),
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
            "(e.g. '@/.donna/session/plans/artifact_id_filepaths.donna.md:finish')."
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
