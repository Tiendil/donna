import pytest
from llm_tool_cli.core.result import Err, Result
from llm_tool_cli.protocol.logic_cells import EnvironmentErrorCell

from donna.domain.ids import SectionId
from donna.machine import errors as machine_errors
from donna.machine.artifacts import Artifact, ArtifactNode, ArtifactSectionMeta, ArtifactSectionNode
from donna.machine.context import reset_context, set_context
from donna.machine.primitives import Primitive
from donna.machine.tests import make
from donna.machine.tests.helpers import FakeMachineContext
from donna.protocol import ArtifactInfoCell, ArtifactSectionStatusCell, ArtifactStatusCell


class _Meta(ArtifactSectionMeta):
    def cells_meta(self) -> dict[str, str]:
        return {"custom": "value"}


class _RejectingPrimitive(Primitive):
    def validate_section(self, artifact: Artifact, section_id: SectionId) -> Result[None]:
        return Err([machine_errors.PrimitiveInvalidImportPath(import_path="bad")])


class TestArtifactSectionMeta:
    def test_cells_meta__returns_empty_metadata(self) -> None:
        assert ArtifactSectionMeta().cells_meta() == {}


class TestArtifactSection:

    def test_node__returns_artifact_section_node(self) -> None:
        section = make.artifact_section()

        assert isinstance(section.node(), ArtifactSectionNode)


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
        machine_context = FakeMachineContext(primitive=Primitive())
        token = set_context(machine_context)

        try:
            result = artifact.validate_artifact()
        finally:
            reset_context(token)

        assert result.is_ok()
        assert machine_context.primitives.resolved == [make.PRIMITIVE_PATH]

    def test_validate_artifact__collects_primary_and_section_errors(self) -> None:
        artifact = make.artifact([make.artifact_section(primary=False)])
        machine_context = FakeMachineContext(primitive=_RejectingPrimitive())
        token = set_context(machine_context)

        try:
            result = artifact.validate_artifact()
        finally:
            reset_context(token)

        assert result.is_err()
        errors = result.unwrap_err()
        assert [type(error) for error in errors] == [
            machine_errors.ArtifactPrimarySectionMissing,
            machine_errors.PrimitiveInvalidImportPath,
        ]

    def test_node__returns_artifact_node(self) -> None:
        assert isinstance(make.artifact().node(), ArtifactNode)


class TestArtifactNode:
    def test_status__returns_primary_section_summary(self) -> None:
        cell = make.artifact().node().status()

        assert isinstance(cell, ArtifactStatusCell)
        assert cell.artifact_id == make.ARTIFACT_ID
        assert cell.artifact_kind == make.PRIMITIVE_PATH
        assert cell.artifact_title == "Workflow"
        assert cell.description == "Workflow description"

    def test_info__returns_typed_artifact_sections(self) -> None:
        primary = make.artifact_section(primary=True)
        secondary = make.artifact_section(id=make.SECONDARY_SECTION_ID, title="Next", description="Body")
        cell = make.artifact([primary, secondary]).node().info()

        assert isinstance(cell, ArtifactInfoCell)
        assert cell.artifact_id == make.ARTIFACT_ID
        assert cell.artifact_kind == make.PRIMITIVE_PATH
        assert cell.title == primary.title
        assert cell.description == primary.description
        assert [(section.section_id, section.title, section.description) for section in cell.sections] == [
            (secondary.id, secondary.title, secondary.description),
        ]

    @pytest.mark.parametrize("view", ["status", "info"])
    @pytest.mark.parametrize("count", [0, 2])
    def test_views__return_typed_error_for_invalid_primary_sections(self, view: str, count: int) -> None:
        sections = [make.artifact_section(id=SectionId(f"section_{index}"), primary=True) for index in range(count)]
        artifact = make.artifact(sections)

        cell = getattr(artifact.node(), view)()

        assert isinstance(cell, EnvironmentErrorCell)
        assert cell.error == artifact.primary_section().unwrap_err()[0]

    def test_components__returns_section_nodes(self) -> None:
        components = make.artifact().node().components()

        assert len(components) == 1
        assert isinstance(components[0], ArtifactSectionNode)


class TestArtifactSectionNode:
    def test_status__returns_section_status_cell(self) -> None:
        section = make.artifact_section(primary=True, meta=_Meta())

        cell = ArtifactSectionNode(section).status()

        assert isinstance(cell, ArtifactSectionStatusCell)
        assert cell.artifact_id == section.artifact_id
        assert cell.section_id == section.id
        assert cell.section_kind == section.kind
        assert cell.section_primary
        assert cell.title == section.title
        assert cell.description == section.description
        assert cell.extra_meta == {"custom": "value"}
