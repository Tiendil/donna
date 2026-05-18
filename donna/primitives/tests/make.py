from typing import cast

from donna.context.tests.helpers import FakeJournal, FakeOutputEmitter
from donna.domain.artifact_ids import ArtifactSectionId
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.ids import SectionId
from donna.domain.python_path import PythonPath
from donna.machine.templates_context import DirectiveContext


def primitive_kind(path: str) -> PythonPath:
    return PythonPath(NormalizedRawIdPath(path))


def section_id(value: str) -> SectionId:
    return SectionId(value)


def operation_id(section: str) -> ArtifactSectionId:
    return ArtifactSectionId(f"@/workflows/test.donna.md:{section}")


def template_context(**values: object) -> DirectiveContext:
    return cast(DirectiveContext, values)


class FakeRuntimeContext:
    def __init__(self) -> None:
        self.output = FakeOutputEmitter()
        self.journal = FakeJournal()
