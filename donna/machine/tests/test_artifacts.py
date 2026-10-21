import pytest
from llm_tool_cli.core.result import Err, Result
from llm_tool_cli.protocol.logic_cells import EnvironmentErrorCell

from donna.domain.ids import SectionId
from donna.machine import errors as machine_errors
from donna.machine.artifacts import Artifact
from donna.machine.primitives import Primitive
from donna.machine.tests import make
from donna.machine.tests.helpers import MachineServices, services_scope
from donna.protocol import ArtifactStatusCell


class _RejectingPrimitive(Primitive):
    def validate_section(self, artifact: Artifact, section_id: SectionId) -> Result[None]:
        return Err([machine_errors.PrimitiveInvalidImportPath(import_path="bad")])


class TestArtifact:
    def test_primary_section__returns_single_primary_section(self) -> None:
        primary = make.artifact_section(primary=True)
        secondary = make.artifact_section(id=make.SECONDARY_SECTION_ID)

        result = make.artifact([secondary, primary]).primary_section()

        assert result.is_ok()
        assert result.unwrap() == primary

    def test_primary_section__reports_missing_primary_section(self) -> None:
        result = make.artifact([make.artifact_section(primary=False)]).primary_section()

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.ArtifactPrimarySectionMissing)
        assert error.artifact_id == make.ARTIFACT_ID

    def test_primary_section__reports_multiple_primary_sections(self) -> None:
        first = make.artifact_section(id=SectionId("z"), primary=True)
        second = make.artifact_section(id=SectionId("a"), primary=True)

        result = make.artifact([first, second]).primary_section()

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.MultiplePrimarySectionsError)
        assert error.primary_sections == [SectionId("a"), SectionId("z")]

    def test_get_section__returns_primary_section_for_none(self) -> None:
        artifact = make.artifact()

        result = artifact.get_section(None)

        assert result.is_ok()
        assert result.unwrap().id == make.PRIMARY_SECTION_ID

    def test_get_section__returns_requested_section(self) -> None:
        secondary = make.artifact_section(id=make.SECONDARY_SECTION_ID)
        artifact = make.artifact([make.artifact_section(primary=True), secondary])

        result = artifact.get_section(make.SECONDARY_SECTION_ID)

        assert result.is_ok()
        assert result.unwrap() == secondary

    def test_get_section__reports_missing_section(self) -> None:
        artifact = make.artifact()

        result = artifact.get_section(make.SECONDARY_SECTION_ID)

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.ArtifactSectionNotFound)
        assert error.section_id == make.SECONDARY_SECTION_ID

    def test_get_section_number__returns_zero_based_index(self) -> None:
        artifact = make.artifact(
            [
                make.artifact_section(primary=True),
                make.artifact_section(id=make.SECONDARY_SECTION_ID),
            ]
        )

        assert artifact.get_section_number(make.SECONDARY_SECTION_ID) == 1
        assert artifact.get_section_number(SectionId("missing")) is None

    def test_validate_artifact__accepts_valid_artifact(self) -> None:
        artifact = make.artifact()
        machine_context = MachineServices(primitive=Primitive())

        with services_scope(machine_context):
            result = artifact.validate_artifact()

        assert result.is_ok()
        assert machine_context.primitives.resolved == [make.PRIMITIVE_PATH]

    def test_validate_artifact__collects_primary_and_section_errors(self) -> None:
        artifact = make.artifact([make.artifact_section(primary=False)])
        machine_context = MachineServices(primitive=_RejectingPrimitive())

        with services_scope(machine_context):
            result = artifact.validate_artifact()

        assert result.is_err()
        errors = result.unwrap_err()
        assert [type(error) for error in errors] == [
            machine_errors.ArtifactPrimarySectionMissing,
            machine_errors.PrimitiveInvalidImportPath,
        ]

    def test_status_cell__returns_primary_section_summary(self) -> None:
        cell = make.artifact().status_cell()

        assert isinstance(cell, ArtifactStatusCell)
        assert cell.artifact_id == make.ARTIFACT_ID
        assert cell.artifact_kind == make.PRIMITIVE_PATH
        assert cell.artifact_title == "Workflow"
        assert cell.description == "Workflow description"

    @pytest.mark.parametrize("count", [0, 2])
    def test_status_cell__returns_typed_error_for_invalid_primary_sections(self, count: int) -> None:
        sections = [make.artifact_section(id=SectionId(f"section_{index}"), primary=True) for index in range(count)]
        artifact = make.artifact(sections)

        cell = artifact.status_cell()

        assert isinstance(cell, EnvironmentErrorCell)
        assert cell.error == artifact.primary_section().unwrap_err()[0]
