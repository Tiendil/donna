"""Shared instances for standard library kind definitions."""

from donna.primitives.artifacts.specification import ArtifactSectionTextKind, SpecificationKind
from donna.primitives.artifacts.workflow import WorkflowKind
from donna.primitives.directives.goto import GoTo
from donna.primitives.directives.view import View
from donna.primitives.operations.finish_workflow import FinishWorkflowKind
from donna.primitives.operations.request_action import RequestActionKind

specification = SpecificationKind()
workflow = WorkflowKind()
text = ArtifactSectionTextKind()
request_action = RequestActionKind()
finish = FinishWorkflowKind()

view = View(analyze_id="view")
goto = GoTo(analyze_id="goto")
