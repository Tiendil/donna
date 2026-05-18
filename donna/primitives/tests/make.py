from typing import cast

from donna.context.tests.helpers import FakeJournal, FakeOutputEmitter
from donna.domain.artifact_ids import ArtifactSectionId
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.ids import SectionId
from donna.domain.python_path import PythonPath
from donna.machine.templates_context import DirectiveContext

WORKFLOW_SECTION_ID = SectionId("workflow")
START_SECTION_ID = SectionId("start")
NEXT_SECTION_ID = SectionId("next")
DONE_SECTION_ID = SectionId("done")
OTHER_SECTION_ID = SectionId("other")
START_OPERATION_ID = ArtifactSectionId("@/workflows/test.donna.md:start")

WORKFLOW_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.artifacts.workflow.Workflow"))
TEXT_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.text.Text"))
REQUEST_ACTION_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.request_action.RequestAction"))
OUTPUT_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.output.Output"))
RUN_SCRIPT_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.run_script.RunScript"))
FINISH_WORKFLOW_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.finish_workflow.FinishWorkflow"))


def template_context(**values: object) -> DirectiveContext:
    return cast(DirectiveContext, values)


class FakeRuntimeContext:
    def __init__(self) -> None:
        self.output = FakeOutputEmitter()
        self.journal = FakeJournal()
