import pathlib

from donna.core import errors as core_errors
from donna.domain.ids import ArtifactId, FullArtifactId, WorldId


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.workspaces."""


class WorldError(core_errors.EnvironmentError):
    cell_kind: str = "world_error"


class WorldConfigError(WorldError):
    cell_kind: str = "world_config_error"
    config_path: pathlib.Path

    def content_intro(self) -> str:
        return f"Error in world config file '{self.config_path}'"


class ConfigParseFailed(WorldConfigError):
    code: str = "donna.workspaces.config_parse_failed"
    message: str = "Failed to parse config file: {error.details}"
    details: str


class ConfigValidationFailed(WorldConfigError):
    code: str = "donna.workspaces.config_validation_failed"
    message: str = "Failed to validate config file: {error.details}"
    details: str


class WorkspaceAlreadyInitialized(WorldError):
    code: str = "donna.workspaces.workspace_already_initialized"
    message: str = "Workspace already initialized at `{error.project_dir}`"
    ways_to_fix: list[str] = [
        "Continue using the existing workspace.",
        "Remove the existing `.donna` directory if you want to reinitialize.",
        "Choose a different project directory.",
    ]
    project_dir: pathlib.Path


class WorldNotConfigured(WorldError):
    code: str = "donna.workspaces.world_not_configured"
    message: str = "World with id `{error.world_id}` is not configured"
    world_id: WorldId


class SourceConfigNotConfigured(WorldError):
    code: str = "donna.workspaces.source_config_not_configured"
    message: str = "Source config `{error.kind}` is not configured"
    kind: str


class WorldReadonly(WorldError):
    code: str = "donna.workspaces.world_readonly"
    message: str = "World `{error.world_id}` is read-only"
    ways_to_fix: list[str] = [
        "Use a world configured with readonly = false. Most likely they are `project` and `session`.",
    ]
    world_id: WorldId


class WorldStateStorageUnsupported(WorldError):
    code: str = "donna.workspaces.state_storage_unsupported"
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
    code: str = "donna.workspaces.artifact_not_found"
    message: str = "Artifact `{error.artifact_id}` does not exist in world `{error.world_id}`"
    ways_to_fix: list[str] = [
        "Check the artifact id for typos.",
        "Ensure the artifact exists in the specified world.",
    ]


class ArtifactMultipleFiles(ArtifactError):
    code: str = "donna.workspaces.artifact_multiple_files"
    message: str = "Artifact `{error.artifact_id}` has multiple files in world `{error.world_id}`"
    ways_to_fix: list[str] = [
        "Keep a single source file per artifact in the world.",
    ]


class UnsupportedArtifactSourceExtension(ArtifactError):
    code: str = "donna.workspaces.unsupported_artifact_source_extension"
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


class TemplateDirectiveError(WorldError):
    cell_kind: str = "template_directive_error"
    artifact_id: FullArtifactId | None = None

    def content_intro(self) -> str:
        if self.artifact_id is None:
            return "Error in template directive"

        return f"Error in template directive for artifact '{self.artifact_id}'"


class DirectivePathIncomplete(TemplateDirectiveError):
    code: str = "donna.workspaces.directive_path_incomplete"
    message: str = "Directive path must include module and directive parts, got `{error.path}`."
    ways_to_fix: list[str] = ["Use a directive path with both module and directive names."]
    path: str


class DirectiveModuleNotImportable(TemplateDirectiveError):
    code: str = "donna.workspaces.directive_module_not_importable"
    message: str = "Directive module `{error.module_path}` is not importable."
    ways_to_fix: list[str] = [
        "Check the module path for typos.",
        "Ensure the module exists and is importable in the current environment.",
    ]
    module_path: str


class DirectiveNotAvailable(TemplateDirectiveError):
    code: str = "donna.workspaces.directive_not_available"
    message: str = "Directive `{error.module_path}.{error.directive_name}` is not available."
    ways_to_fix: list[str] = [
        "Check the directive name for typos.",
        "Ensure the directive is defined in the module.",
    ]
    module_path: str
    directive_name: str


class DirectiveNotDirective(TemplateDirectiveError):
    code: str = "donna.workspaces.directive_not_directive"
    message: str = "`{error.module_path}.{error.directive_name}` is not a directive."
    ways_to_fix: list[str] = [
        "Check the directive path for typos.",
        "Check if you use the right primitive for the task.",
        "Ensure the referenced object is a `donna.machine.templates.Directive` instance.",
    ]
    module_path: str
    directive_name: str


class DirectiveUnexpectedError(TemplateDirectiveError):
    code: str = "donna.workspaces.directive_unexpected_error"
    message: str = "Unexpected error while applying directive `{error.directive_path}`: {error.details}"
    ways_to_fix: list[str] = [
        "Check the documentation for the directive to ensure correct usage.",
        "Ask the developer to help debug the issue.",
    ]
    directive_path: str
    details: str


class MarkdownUnsupportedCodeFormat(MarkdownError):
    code: str = "donna.workspaces.markdown_unsupported_code_format"
    message: str = "Unsupported code block format `{error.format}`"
    ways_to_fix: list[str] = [
        "Use one of the supported formats: json, yaml, yml, toml.",
    ]
    format: str


class MarkdownMultipleH1Sections(MarkdownError):
    code: str = "donna.workspaces.markdown_multiple_h1_sections"
    message: str = "Multiple H1 sections are not supported"
    ways_to_fix: list[str] = [
        "Keep a single H1 section in the artifact.",
    ]


class MarkdownH1SectionMustBeFirst(MarkdownError):
    code: str = "donna.workspaces.markdown_h1_section_must_be_first"
    message: str = "H1 section must be the first section in the artifact"
    ways_to_fix: list[str] = [
        "Ensure the H1 section is the first section in the artifact.",
    ]


class MarkdownArtifactWithoutSections(MarkdownError):
    code: str = "donna.workspaces.markdown_artifact_without_sections"
    message: str = "Artifact MUST have at least one section"


class PrimitiveDoesNotSupportMarkdown(MarkdownError):
    code: str = "donna.workspaces.primitive_does_not_support_markdown"
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
