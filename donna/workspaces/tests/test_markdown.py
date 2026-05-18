from markdown_it import MarkdownIt

from donna.workspaces import errors as workspace_errors
from donna.workspaces import markdown
from donna.workspaces.markdown import SectionLevel
from donna.workspaces.tests import make


class TestSectionLevel:
    def test_values__match_supported_heading_levels(self) -> None:
        assert SectionLevel.h1 == "h1"
        assert SectionLevel.h2 == "h2"


class TestCodeSource:
    def test_structured_data__parses_supported_formats(self) -> None:
        assert make.code_source("json", '{"value": 1}').structured_data().unwrap() == {"value": 1}
        assert make.code_source("yaml", "value: 1").structured_data().unwrap() == {"value": 1}
        assert make.code_source("yml", "value: 1").structured_data().unwrap() == {"value": 1}
        assert make.code_source("toml", "value = 1").structured_data().unwrap() == {"value": 1}

    def test_structured_data__script_blocks_return_empty_config(self) -> None:
        assert make.code_source("python", "print(1)", script=True).structured_data().unwrap() == {}

    def test_structured_data__rejects_unsupported_format(self) -> None:
        result = make.code_source("ini", "value=1", config=True).structured_data()

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.MarkdownUnsupportedCodeFormat)
        assert error.format == "ini"


class TestSectionSource:
    def test_as_original_markdown__renders_title_and_original_tokens(self) -> None:
        tokens = MarkdownIt("commonmark").parse("Body\n")
        section = make.section_source(level=SectionLevel.h1, title="Workflow")
        section.original_tokens.extend(tokens)

        assert section.as_original_markdown(with_title=True).startswith("# Workflow\n")
        assert "Body" in section.as_original_markdown(with_title=False)

    def test_as_analysis_markdown__renders_title_and_analysis_tokens(self) -> None:
        tokens = MarkdownIt("commonmark").parse("Analysis\n")
        section = make.section_source(level=SectionLevel.h2, title="Step")
        section.analysis_tokens.extend(tokens)

        assert section.as_analysis_markdown(with_title=True).startswith("## Step\n")
        assert "Analysis" in section.as_analysis_markdown(with_title=False)

    def test_config__returns_empty_dict_without_config_blocks(self) -> None:
        assert make.section_source().config().unwrap() == {}

    def test_config__returns_single_config_block_data(self) -> None:
        section = make.section_source(configs=[make.code_source("toml", "id = 'section'", config=True)])

        assert section.config().unwrap() == {"id": "section"}

    def test_config__rejects_multiple_config_blocks(self) -> None:
        section = make.section_source(
            configs=[
                make.code_source("toml", "id = 'first'", config=True),
                make.code_source("toml", "id = 'second'", config=True),
            ]
        )

        result = section.config()

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.MarkdownMultipleConfigBlocksInSection)

    def test_script__returns_none_without_script_blocks(self) -> None:
        assert make.section_source().script().unwrap() is None

    def test_script__returns_single_script_block_content(self) -> None:
        section = make.section_source(configs=[make.code_source("python", "print(1)", script=True)])

        assert section.script().unwrap() == "print(1)"

    def test_script__rejects_multiple_script_blocks(self) -> None:
        section = make.section_source(
            configs=[
                make.code_source("python", "print(1)", script=True),
                make.code_source("python", "print(2)", script=True),
            ]
        )

        result = section.script()

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.MarkdownMultipleScriptBlocksInSection)


class TestRenderBack:
    def test_renders_tokens_to_markdown(self) -> None:
        tokens = MarkdownIt("commonmark").parse("Body\n")

        assert "Body" in markdown.render_back(tokens)


class TestClearHeading:
    def test_removes_heading_markers_and_surrounding_whitespace(self) -> None:
        assert markdown.clear_heading("##  Step  ") == "Step"


class TestParseH1:
    def test_parse_h1__creates_primary_section(self) -> None:
        result = markdown.parse("# Workflow\n", artifact_id=make.ARTIFACT_ID)

        assert result.is_ok()
        section = result.unwrap()[0]
        assert section.level == SectionLevel.h1
        assert section.title == "Workflow"


class TestParseH2:
    def test_parse_h2__creates_tail_section_after_h1(self) -> None:
        result = markdown.parse("# Workflow\n\n## Step\n", artifact_id=make.ARTIFACT_ID)

        assert result.is_ok()
        section = result.unwrap()[1]
        assert section.level == SectionLevel.h2
        assert section.title == "Step"


class TestParseHeading:
    def test_parse_heading__stores_lower_headings_as_section_content(self) -> None:
        result = markdown.parse("# Workflow\n\n### Detail\n", artifact_id=make.ARTIFACT_ID)

        assert result.is_ok()
        assert "### Detail" in result.unwrap()[0].as_original_markdown(with_title=False)


class TestParseFence:
    def test_parse_fence__keeps_non_donna_fences_in_original_tokens(self) -> None:
        result = markdown.parse("# Workflow\n\n```python\nprint(1)\n```\n", artifact_id=make.ARTIFACT_ID)

        assert result.is_ok()
        section = result.unwrap()[0]
        assert section.configs == []
        assert "print(1)" in section.as_original_markdown(with_title=False)

    def test_parse_fence__treats_plain_donna_marker_as_config(self) -> None:
        result = markdown.parse("# Workflow\n\n```toml donna\nid = 'primary'\n```\n", artifact_id=make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap()[0].config().unwrap() == {"id": "primary"}

    def test_parse_fence__parses_marker_key_values(self) -> None:
        result = markdown.parse(
            "# Workflow\n\n```toml donna name=value\nid = 'primary'\n```\n", artifact_id=make.ARTIFACT_ID
        )

        assert result.is_ok()
        assert result.unwrap()[0].configs[0].properties["name"] == "value"


class TestParseNested:
    def test_parse_nested__keeps_nested_blocks_in_section_content(self) -> None:
        result = markdown.parse("# Workflow\n\n> Quote\n", artifact_id=make.ARTIFACT_ID)

        assert result.is_ok()
        assert "> Quote" in result.unwrap()[0].as_original_markdown(with_title=False)


class TestParseOthers:
    def test_parse_others__keeps_paragraphs_in_section_content(self) -> None:
        result = markdown.parse("# Workflow\n\nBody\n", artifact_id=make.ARTIFACT_ID)

        assert result.is_ok()
        assert "Body" in result.unwrap()[0].as_original_markdown(with_title=False)


class TestParse:
    def test_parse__extracts_h1_h2_content_and_donna_config_blocks(self) -> None:
        result = markdown.parse(
            """# Workflow

Intro

```toml donna
id = "primary"
```

## Step

Body

```python donna script
print("run")
```
""",
            artifact_id=make.ARTIFACT_ID,
        )

        assert result.is_ok()
        sections = result.unwrap()
        assert [section.level for section in sections] == [SectionLevel.h1, SectionLevel.h2]
        assert [section.title for section in sections] == ["Workflow", "Step"]
        assert sections[0].config().unwrap() == {"id": "primary"}
        assert sections[1].script().unwrap() == 'print("run")'
        assert "Intro" in sections[0].as_original_markdown(with_title=False)
        assert "Body" in sections[1].as_original_markdown(with_title=False)

    def test_parse__rejects_h2_before_h1(self) -> None:
        result = markdown.parse("## Step\n", artifact_id=make.ARTIFACT_ID)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.MarkdownH1SectionMustBeFirst)

    def test_parse__rejects_multiple_h1_sections(self) -> None:
        result = markdown.parse("# First\n\n# Second\n", artifact_id=make.ARTIFACT_ID)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.MarkdownMultipleH1Sections)
