import pathlib

from donna.core import errors as core_errors
from donna.domain.ids import ArtifactId, FullArtifactId, WorldId


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.world."""


class WorldError(core_errors.EnvironmentError):
    cell_kind: str = "world_error"


class WorldConfigError(WorldError):
    cell_kind: str = "world_config_error"
    config_path: pathlib.Path

    def content_intro(self) -> str:
        return f"Error in world config file '{self.config_path}'"


class ConfigParseFailed(WorldConfigError):
    code: str = "donna.world.config_parse_failed"
    message: str = "Failed to parse config file: {error.details}"
    details: str


class ConfigValidationFailed(WorldConfigError):
    code: str = "donna.world.config_validation_failed"
    message: str = "Failed to validate config file: {error.details}"
    details: str


class WorldNotConfigured(WorldError):
    code: str = "donna.world.world_not_configured"
    message: str = "World with id `{error.world_id}` is not configured"
    world_id: WorldId


class SourceConfigNotConfigured(WorldError):
    code: str = "donna.world.source_config_not_configured"
    message: str = "Source config `{error.kind}` is not configured"
    kind: str


class WorldReadonly(WorldError):
    code: str = "donna.world.world_readonly"
    message: str = "World `{error.world_id}` is read-only"
    ways_to_fix: list[str] = [
        "Use a world configured with readonly = false. Most likely they are `project` and `session`.",
    ]
    world_id: WorldId


class WorldStateStorageUnsupported(WorldError):
    code: str = "donna.world.state_storage_unsupported"
    message: str = "World `{error.world_id}` does not support state storage"
    ways_to_fix: list[str] = [
        "Use the session world.",
    ]
    world_id: WorldId


class ArtifactError(WorldError):
    cell_kind: str = "artifact_error"
    artifact_id: ArtifactId
    world_id: WorldId

    def content_intro(self) -> str:
        return f"Error for artifact '{self.artifact_id}' in world '{self.world_id}'"


class ArtifactNotFound(ArtifactError):
    code: str = "donna.world.artifact_not_found"
    message: str = "Artifact `{error.artifact_id}` does not exist in world `{error.world_id}`"
    ways_to_fix: list[str] = [
        "Check the artifact id for typos.",
        "Ensure the artifact exists in the specified world.",
    ]


class ArtifactMultipleFiles(ArtifactError):
    code: str = "donna.world.artifact_multiple_files"
    message: str = "Artifact `{error.artifact_id}` has multiple files in world `{error.world_id}`"
    ways_to_fix: list[str] = [
        "Keep a single source file per artifact in the world.",
    ]


class UnsupportedArtifactSourceExtension(ArtifactError):
    code: str = "donna.world.unsupported_artifact_source_extension"
    message: str = "Unsupported artifact source extension `{error.extension}` in world `{error.world_id}`"
    ways_to_fix: list[str] = [
        "Use a supported extension for the configured sources.",
    ]
    extension: str


class MarkdownError(WorldError):
    cell_kind: str = "markdown_error"
    artifact_id: FullArtifactId | None = None

    def content_intro(self) -> str:
        if self.artifact_id is None:
            return "Error in markdown source"

        return f"Error in markdown artifact '{self.artifact_id}'"


class MarkdownUnsupportedCodeFormat(MarkdownError):
    code: str = "donna.world.markdown_unsupported_code_format"
    message: str = "Unsupported code block format `{error.format}`"
    ways_to_fix: list[str] = [
        "Use one of the supported formats: json, yaml, yml, toml.",
    ]
    format: str


class MarkdownMultipleH1Sections(MarkdownError):
    code: str = "donna.world.markdown_multiple_h1_sections"
    message: str = "Multiple H1 sections are not supported"
    ways_to_fix: list[str] = [
        "Keep a single H1 section in the artifact.",
    ]


class MarkdownMultipleH1Titles(MarkdownError):
    code: str = "donna.world.markdown_multiple_h1_titles"
    message: str = "Multiple H1 titles are not supported"
    ways_to_fix: list[str] = [
        "Keep a single H1 title in the artifact.",
    ]


class MarkdownH2BeforeH1Title(MarkdownError):
    code: str = "donna.world.markdown_h2_before_h1_title"
    message: str = "H2 section found before H1 title"
    ways_to_fix: list[str] = [
        "Ensure the first heading is an H1 title before any H2 sections.",
    ]


class MarkdownArtifactWithoutSections(MarkdownError):
    code: str = "donna.world.markdown_artifact_without_sections"
    message: str = "Artifact MUST have at least one section"


class PrimitiveDoesNotSupportMarkdown(MarkdownError):
    code: str = "donna.world.primitive_does_not_support_markdown"
    message: str = "Primitive {error.primitive_id} cannot construct artifact section from the Markdown source"
    ways_to_fix: list[str] = [
        "Ensure the section kind points to a primitive that supports Markdown sections.",
    ]
    primitive_id: str


class MarkdownSectionsCountMismatch(InternalError):
    message = (
        "Artifact `{artifact_id}` has {original_count} sections in the original render "
        "and {analyzed_count} sections in the analysis render."
    )


class GlobalConfigAlreadySet(InternalError):
    message = "Global config value is already set"


class GlobalConfigNotSet(InternalError):
    message = "Global config value is not set"
