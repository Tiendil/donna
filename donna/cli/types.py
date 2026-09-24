import pathlib
from typing import Annotated, NoReturn

import typer
from llm_tool_cli.core.errors import EnvironmentErrors

from donna.cli.utils import output_cells
from donna.domain import errors as domain_errors
from donna.domain.artifact_ids import (
    ARTIFACT_SECTION_DELIMITER,
    ArtifactId,
    ArtifactSectionId,
)
from donna.domain.constants import DONNA_ARTIFACT_EXTENSION
from donna.domain.internal_ids import ActionRequestId
from donna.domain.paths import PathInput, UntrustedPath
from donna.machine.templates import RenderMode
from donna.protocol.errors import environment_error_node
from donna.protocol.modes import Mode
from donna.workspaces import paths as workspace_paths
from donna.workspaces.artifacts import has_donna_artifact_extension


def _exit_with_errors(errors: EnvironmentErrors) -> NoReturn:
    output_cells([environment_error_node(error).info() for error in errors])
    raise typer.Exit(code=0)


def _parse_raw_artifact_path(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise typer.BadParameter("Artifact path must not be empty.")
    return normalized


def _artifact_filename(value: str) -> str:
    return pathlib.PurePosixPath(value.split(ARTIFACT_SECTION_DELIMITER, maxsplit=1)[0]).name


def parse_artifact_id_argument(value: str, project_root: PathInput) -> ArtifactId:
    artifact_path = workspace_paths.normalize_artifact_path(
        value, UntrustedPath(project_root), cwd=UntrustedPath(pathlib.Path.cwd())
    )
    if artifact_path is None:
        _exit_with_errors([domain_errors.InvalidIdFormat(id_type=ArtifactId.__name__, value=value)])

    if not has_donna_artifact_extension(_artifact_filename(artifact_path)):
        raise typer.BadParameter(
            f"Unsupported artifact extension for '{artifact_path}'. Use '*{DONNA_ARTIFACT_EXTENSION}'."
        )

    artifact_id = workspace_paths.normalize_artifact_id(
        value, UntrustedPath(project_root), cwd=UntrustedPath(pathlib.Path.cwd())
    )
    if artifact_id is None:
        _exit_with_errors([domain_errors.InvalidIdFormat(id_type=ArtifactId.__name__, value=value)])

    return artifact_id


def parse_artifact_section_id_argument(value: str, project_root: PathInput) -> ArtifactSectionId:
    section_id = workspace_paths.normalize_artifact_section_id(
        value, UntrustedPath(project_root), cwd=UntrustedPath(pathlib.Path.cwd())
    )
    if section_id is None:
        _exit_with_errors([domain_errors.InvalidIdFormat(id_type=f"{ArtifactSectionId.__name__} format", value=value)])

    return section_id


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


def _parse_input_path(value: str) -> UntrustedPath:
    normalized = value.strip()
    if normalized == "-":
        return UntrustedPath(pathlib.Path("-"))

    path = pathlib.Path(normalized).expanduser()
    if not path.exists():
        raise typer.BadParameter(f"Input path '{value}' does not exist.")
    if not path.is_file():
        raise typer.BadParameter(f"Input path '{value}' is not a file.")

    if not path.is_absolute():
        path = path.resolve()

    return UntrustedPath(path)


ActionRequestIdArgument = Annotated[
    ActionRequestId,
    typer.Argument(
        parser=_parse_action_request_id,
        help="Action request ID (for example: AR-12-x).",
    ),
]


ArtifactIdArgument = Annotated[
    str,
    typer.Argument(
        parser=_parse_raw_artifact_path,
        help=(
            "Artifact path with the Donna artifact extension "
            "(e.g., '@/workflows/polish.donna.md' or './workflows/polish.donna.md')."
        ),
    ),
]


ArtifactIdsArgument = Annotated[
    list[str] | None,
    typer.Argument(
        parser=_parse_raw_artifact_path,
        help=(
            "Artifact paths with the Donna artifact extension "
            "(e.g., '@/workflows/polish.donna.md' or './workflows/polish.donna.md')."
        ),
    ),
]


ArtifactSectionIdArgument = Annotated[
    str,
    typer.Argument(
        parser=_parse_raw_artifact_path,
        help=(
            "Artifact section path in 'artifact:section' form "
            "(e.g. '@/.session/donna/plans/artifact_id_filepaths.donna.md:finish')."
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

RenderModeOption = Annotated[
    RenderMode,
    typer.Option(
        "--mode",
        help="Artifact render mode to use. Examples: --mode=view, --mode=execute, --mode=analysis.",
    ),
]


ConfigOption = Annotated[
    pathlib.Path | None,
    typer.Option(
        "--config",
        file_okay=True,
        dir_okay=False,
        exists=False,
        help="Optional project config file. If omitted, Donna discovers donna.toml by searching parent directories.",
    ),
]

InputPathArgument = Annotated[
    UntrustedPath,
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
