from typing import ClassVar

from pytest_mock import MockerFixture

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.artifact_ids import ArtifactId
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.ids import SectionId
from donna.domain.python_path import PythonPath
from donna.machine.artifacts import Artifact, ArtifactSection, ArtifactSectionConfig
from donna.machine.primitives import Primitive
from donna.primitives.sections.text import Text
from donna.workspaces import errors as workspace_errors
from donna.workspaces import markdown_parser
from donna.workspaces.artifacts import RENDER_CONTEXT_VIEW
from donna.workspaces.markdown import CodeSource, SectionLevel, SectionSource
from donna.workspaces.markdown_parser import MarkdownSectionMixin, construct_sections_from_markdown
from donna.workspaces.tests import make

TEXT_KIND = PythonPath(NormalizedRawIdPath("donna.primitives.sections.text.Text"))
LIB_TEXT_KIND = PythonPath(NormalizedRawIdPath("donna.lib.text"))


class _MarkdownPrimitive(MarkdownSectionMixin, Primitive):
    config_class: ClassVar[type[ArtifactSectionConfig]] = ArtifactSectionConfig


class _FailingMarkdownPrimitive(_MarkdownPrimitive):
    def markdown_construct_section(
        self,
        artifact_id: ArtifactId,
        source: SectionSource,
        config: dict[str, object],
        primary: bool = False,
    ) -> Result[ArtifactSection, ErrorsList]:
        return Err([workspace_errors.MarkdownArtifactWithoutSections(artifact_id=artifact_id)])


class TestMarkdownSectionConstructor:
    def test_protocol__documents_markdown_construct_section_contract(self) -> None:
        assert hasattr(markdown_parser.MarkdownSectionConstructor, "markdown_construct_section")


class TestMarkdownSectionMixin:
    def test_markdown_build_title__uses_source_title_or_empty_string(self) -> None:
        primitive = _MarkdownPrimitive()

        assert (
            primitive.markdown_build_title(make.ARTIFACT_ID, make.section_source(title="Title"), make.section_config())
            == "Title"
        )
        assert (
            primitive.markdown_build_title(make.ARTIFACT_ID, make.section_source(title=None), make.section_config())
            == ""
        )

    def test_markdown_build_description__uses_original_markdown_without_title(self) -> None:
        primitive = _MarkdownPrimitive()
        source = make.section_source()

        assert primitive.markdown_build_description(make.ARTIFACT_ID, source, make.section_config()) == ""

    def test_markdown_construct_meta__returns_empty_meta(self) -> None:
        primitive = _MarkdownPrimitive()

        result = primitive.markdown_construct_meta(make.ARTIFACT_ID, make.section_source(), make.section_config(), "")

        assert result.is_ok()
        assert result.unwrap().cells_meta() == {}

    def test_markdown_construct_section__builds_artifact_section(self) -> None:
        primitive = _MarkdownPrimitive()

        result = primitive.markdown_construct_section(
            artifact_id=make.ARTIFACT_ID,
            source=make.section_source(title="Section"),
            config={"id": "section", "kind": str(TEXT_KIND)},
        )

        assert result.is_ok()
        section = result.unwrap()
        assert section.id == SectionId("section")
        assert section.kind == TEXT_KIND
        assert section.title == "Section"
        assert not section.primary


class TestParseArtifactContent:
    def test_returns_original_sections_with_analysis_tokens(self) -> None:
        result = markdown_parser.parse_artifact_content(make.ARTIFACT_ID, "# Workflow\n\nBody\n", RENDER_CONTEXT_VIEW)

        assert result.is_ok()
        section = result.unwrap()[0]
        assert section.title == "Workflow"
        assert section.analysis_tokens

    def test_returns_error_for_source_without_sections(self) -> None:
        result = markdown_parser.parse_artifact_content(make.ARTIFACT_ID, "", RENDER_CONTEXT_VIEW)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.MarkdownArtifactWithoutSections)

    def test_raises_internal_error_for_analysis_section_count_mismatch(self, mocker: MockerFixture) -> None:
        mocker.patch.object(
            markdown_parser,
            "render",
            side_effect=[Ok("# Workflow\n"), Ok("# Workflow\n\n## Step\n")],
        )

        try:
            markdown_parser.parse_artifact_content(make.ARTIFACT_ID, "# Workflow\n", RENDER_CONTEXT_VIEW)
        except workspace_errors.MarkdownSectionsCountMismatch as error:
            assert error.arguments["original_count"] == 1
            assert error.arguments["analyzed_count"] == 2
        else:
            raise AssertionError("Expected MarkdownSectionsCountMismatch")


class TestConstructArtifactFromBytes:
    def test_decodes_bytes_and_constructs_artifact_from_markdown(self, mocker: MockerFixture) -> None:
        expected = Artifact(id=make.ARTIFACT_ID, sections=[])
        construct = mocker.patch.object(
            markdown_parser,
            "construct_artifact_from_markdown_source",
            return_value=Ok(expected),
        )

        result = markdown_parser.construct_artifact_from_bytes(
            make.ARTIFACT_ID,
            b"# Workflow",
            RENDER_CONTEXT_VIEW,
            default_section_kind=TEXT_KIND,
            default_primary_section_kind=TEXT_KIND,
            default_primary_section_id=SectionId("primary"),
        )

        assert result.is_ok()
        assert result.unwrap() == expected
        construct.assert_called_once()


class TestConstructArtifactFromMarkdownSource:
    def test_constructs_artifact_with_default_primary_and_tail_config(self) -> None:
        result = markdown_parser.construct_artifact_from_markdown_source(
            make.ARTIFACT_ID,
            "# Workflow\n\n## Step\n",
            RENDER_CONTEXT_VIEW,
            default_section_kind=LIB_TEXT_KIND,
            default_primary_section_kind=LIB_TEXT_KIND,
            default_primary_section_id=SectionId("primary"),
        )

        assert result.is_ok()
        artifact = result.unwrap()
        assert artifact.id == make.ARTIFACT_ID
        assert [section.title for section in artifact.sections] == ["Workflow", "Step"]
        assert artifact.sections[0].primary


class TestConstructSectionsFromMarkdown:
    def test_parses_raw_string_kind_at_workspace_boundary(self) -> None:
        section = SectionSource(
            level=SectionLevel.h2,
            title="Section",
            configs=[
                CodeSource(
                    format="toml",
                    properties={"config": True},
                    content='id = "section"\nkind = "donna.primitives.sections.text.Text"',
                )
            ],
            original_tokens=[],
            analysis_tokens=[],
        )

        result = construct_sections_from_markdown(
            artifact_id=ArtifactId("@/workflow.donna.md"),
            sections=[section],
            default_section_kind=TEXT_KIND,
            primitive_overrides={TEXT_KIND: Text()},
        )

        assert result.is_ok()
        constructed_section = result.unwrap()[0]
        assert constructed_section.id == SectionId("section")
        assert constructed_section.kind == TEXT_KIND
        assert constructed_section.title == "Section"

    def test_generates_missing_section_id(self, mocker: MockerFixture) -> None:
        mocker.patch("uuid.uuid4", return_value=type("FakeUuid", (), {"hex": "abc"})())
        section = make.section_source(configs=[CodeSource(format="toml", properties={"config": True}, content="")])

        result = construct_sections_from_markdown(
            artifact_id=make.ARTIFACT_ID,
            sections=[section],
            default_section_kind=TEXT_KIND,
            primitive_overrides={TEXT_KIND: Text()},
        )

        assert result.is_ok()
        assert result.unwrap()[0].id == SectionId("markdownabc")

    def test_collects_section_construction_errors(self) -> None:
        section = make.section_source(configs=[CodeSource(format="toml", properties={"config": True}, content="")])

        result = construct_sections_from_markdown(
            artifact_id=make.ARTIFACT_ID,
            sections=[section],
            default_section_kind=TEXT_KIND,
            primitive_overrides={TEXT_KIND: _FailingMarkdownPrimitive()},
        )

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.MarkdownArtifactWithoutSections)


class TestResolvePrimitive:
    def test_returns_override_when_present(self) -> None:
        primitive = Text()

        result = markdown_parser._resolve_primitive(TEXT_KIND, {TEXT_KIND: primitive})

        assert result.is_ok()
        assert result.unwrap() == primitive

    def test_uses_machine_resolver_without_override(self, mocker: MockerFixture) -> None:
        primitive = Text()
        resolve_primitive = mocker.patch.object(markdown_parser, "resolve_primitive", return_value=Ok(primitive))

        result = markdown_parser._resolve_primitive(TEXT_KIND)

        assert result.is_ok()
        assert result.unwrap() == primitive
        resolve_primitive.assert_called_once_with(TEXT_KIND)


class TestParsePrimitiveId:
    def test_returns_python_path_unchanged(self) -> None:
        result = markdown_parser._parse_primitive_id(TEXT_KIND)

        assert result.is_ok()
        assert result.unwrap() == TEXT_KIND

    def test_parses_string_python_path(self) -> None:
        result = markdown_parser._parse_primitive_id(str(TEXT_KIND))

        assert result.is_ok()
        assert result.unwrap() == TEXT_KIND


class TestEnsureMarkdownConstructible:
    def test_accepts_markdown_section_mixin(self) -> None:
        result = markdown_parser._ensure_markdown_constructible(Text(), TEXT_KIND)

        assert result.is_ok()

    def test_rejects_primitive_without_markdown_support(self) -> None:
        result = markdown_parser._ensure_markdown_constructible(Primitive(), TEXT_KIND)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.PrimitiveDoesNotSupportMarkdown)
