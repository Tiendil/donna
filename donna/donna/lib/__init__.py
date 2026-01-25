"""Shared instances for standard library kind definitions."""

from donna.primitives.artifacts.python import PythonArtifact, PythonModuleSectionKind
from donna.primitives.artifacts.specification import ArtifactSectionTextKind, SpecificationKind
from donna.primitives.artifacts.workflow import WorkflowKind
from donna.primitives.operations.finish_workflow import FinishWorkflowKind
from donna.primitives.operations.request_action import RequestActionKind

specification_kind_entity = SpecificationKind()
workflow_kind_entity = WorkflowKind()
python_artifact_kind = PythonArtifact()

text_section_kind_entity = ArtifactSectionTextKind()
python_module_section_kind_entity = PythonModuleSectionKind()
request_action_kind_entity = RequestActionKind()
finish_workflow_kind_entity = FinishWorkflowKind()
