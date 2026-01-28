from donna.core import errors as core_errors
from donna.domain.ids import ActionRequestId, ArtifactSectionId, FullArtifactId, FullArtifactSectionId, TaskId


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.machine."""


class PrimitiveMethodUnsupported(InternalError):
    message: str = "Primitive '{primitive_name}' does not support {method_name}."
    primitive_name: str
    method_name: str


class EnvironmentError(core_errors.EnvironmentError):
    """Base class for environment errors in donna.machine."""

    cell_kind: str = "machine_error"


class SessionStateNotInitialized(EnvironmentError):
    code: str = "donna.machine.session_state_not_initialized"
    message: str = "Session state is not initialized."
    ways_to_fix: list[str] = ["Run Donna session start to initialize session state."]


class ActionRequestNotFound(EnvironmentError):
    code: str = "donna.machine.action_request_not_found"
    message: str = "Action request `{error.request_id}` was not found in the current session state."
    ways_to_fix: list[str] = ["Use an action request id from `sessions status` output."]
    request_id: ActionRequestId


class TaskNotFound(EnvironmentError):
    code: str = "donna.machine.task_not_found"
    message: str = "Task `{error.task_id}` was not found in the current session state."
    ways_to_fix: list[str] = ["Ensure the task exists in the current session state before referencing it."]
    task_id: TaskId


class InvalidOperationTransition(EnvironmentError):
    code: str = "donna.machine.invalid_operation_transition"
    message: str = "Operation `{error.operation_id}` cannot transition to `{error.next_operation_id}`."
    ways_to_fix: list[str] = ["Use one of the allowed transitions listed in the action request."]
    operation_id: FullArtifactSectionId
    next_operation_id: FullArtifactSectionId


class WorkflowOperationNotFound(EnvironmentError):
    code: str = "donna.machine.workflow_operation_not_found"
    message: str = "Operation `{error.operation_id}` was not found in its workflow."
    ways_to_fix: list[str] = ["Ensure the workflow contains the referenced operation section."]
    operation_id: FullArtifactSectionId


class PrimitiveInvalidImportPath(EnvironmentError):
    code: str = "donna.machine.primitive_invalid_import_path"
    message: str = "Primitive `{error.import_path}` is not a valid import path."
    ways_to_fix: list[str] = ["Use a full Python import path, e.g. `package.module.ClassName`."]
    import_path: str


class PrimitiveModuleNotImportable(EnvironmentError):
    code: str = "donna.machine.primitive_module_not_importable"
    message: str = "Primitive module `{error.module_path}` is not importable."
    ways_to_fix: list[str] = ["Ensure the module exists and is importable in the current environment."]
    module_path: str


class PrimitiveNotAvailable(EnvironmentError):
    code: str = "donna.machine.primitive_not_available"
    message: str = "Primitive `{error.import_path}` is not available in module `{error.module_path}`."
    ways_to_fix: list[str] = ["Check the primitive name for typos or export it from the module."]
    import_path: str
    module_path: str


class PrimitiveNotPrimitive(EnvironmentError):
    code: str = "donna.machine.primitive_not_primitive"
    message: str = "Primitive `{error.import_path}` is not a Primitive instance."
    ways_to_fix: list[str] = ["Ensure the referenced object is a donna.machine.primitives.Primitive instance."]
    import_path: str


class ArtifactValidationError(EnvironmentError):
    cell_kind: str = "artifact_validation_error"
    artifact_id: FullArtifactId
    section_id: ArtifactSectionId | None = None

    def content_intro(self) -> str:
        if self.section_id:
            return f"Error in artifact '{self.artifact_id}', section '{self.section_id}'"

        return f"Error in artifact '{self.artifact_id}'"


class MultiplePrimarySectionsError(ArtifactValidationError):
    code: str = "donna.artifacts.multiple_primary_sections"
    message: str = "Artifact must have exactly one primary section, found multiple: `{error.primary_sections}`"
    ways_to_fix: list[str] = ["Keep a single h1 section in the artifact."]
    primary_sections: list[ArtifactSectionId]


class ArtifactPrimarySectionMissing(ArtifactValidationError):
    code: str = "donna.artifacts.primary_section_missing"
    message: str = "Artifact must have exactly one primary section, found none."
    ways_to_fix: list[str] = ["Keep a single h1 section in the artifact."]


class ArtifactSectionNotFound(ArtifactValidationError):
    code: str = "donna.artifacts.section_not_found"
    message: str = "Section `{error.section_id}` is not available in artifact `{error.artifact_id}`."
    ways_to_fix: list[str] = ["Check the section id for typos.", "Ensure the section exists in the artifact."]
