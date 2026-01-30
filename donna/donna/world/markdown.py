import enum
from typing import Any

import pydantic
from markdown_it import MarkdownIt
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
from mdformat.renderer import MDRenderer

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import FullArtifactId
from donna.world import errors as world_errors


class SectionLevel(str, enum.Enum):
    h1 = "h1"
    h2 = "h2"


class CodeSource(BaseEntity):
    format: str
    properties: dict[str, str | bool]
    content: str

    def structured_data(self) -> Result[Any, ErrorsList]:
        if "script" in self.properties:
            return Ok({})

        if self.format == "json":
            import json

            return Ok(json.loads(self.content))

        if self.format == "yaml" or self.format == "yml":
            import yaml

            return Ok(yaml.safe_load(self.content))

        if self.format == "toml":
            import tomllib

            return Ok(tomllib.loads(self.content))

        return Err([world_errors.MarkdownUnsupportedCodeFormat(format=self.format)])


class SectionSource(BaseEntity):
    level: SectionLevel
    title: str | None
    configs: list[CodeSource]

    original_tokens: list[Token]
    analysis_tokens: list[Token]

    model_config = pydantic.ConfigDict(frozen=False)

    def _as_markdown(self, tokens: list[Token], with_title: bool) -> str:
        parts = []

        if with_title and self.title is not None:
            match self.level:
                case SectionLevel.h1:
                    prefix = "#"
                case SectionLevel.h2:
                    prefix = "##"

            parts.append(f"{prefix} {self.title}")

        parts.append(render_back(tokens))

        return "\n".join(parts)

    def as_original_markdown(self, with_title: bool) -> str:
        return self._as_markdown(self.original_tokens, with_title)

    def as_analysis_markdown(self, with_title: bool) -> str:
        return self._as_markdown(self.analysis_tokens, with_title)

    def merged_configs(self) -> Result[dict[str, Any], ErrorsList]:
        result: dict[str, Any] = {}
        errors: ErrorsList = []

        for config in self.configs:
            data_result = config.structured_data()
            if data_result.is_err():
                errors.extend(data_result.unwrap_err())
                continue
            result.update(data_result.unwrap())

        if errors:
            return Err(errors)

        return Ok(result)

    def scripts(self) -> list[str]:
        return [config.content for config in self.configs if "script" in config.properties]


def render_back(tokens: list[Token]) -> str:
    renderer = MDRenderer()
    return renderer.render(tokens, {}, {})


def clear_heading(text: str) -> str:
    return text.lstrip("#").strip()


def _parse_h1(
    sections: list[SectionSource], node: SyntaxTreeNode, artifact_id: FullArtifactId | None
) -> Result[SyntaxTreeNode | None, ErrorsList]:
    section = sections[-1]

    if section.level != SectionLevel.h1:
        return Err([world_errors.MarkdownMultipleH1Sections(artifact_id=artifact_id)])

    if section.title is not None:
        return Err([world_errors.MarkdownMultipleH1Titles(artifact_id=artifact_id)])

    section.title = clear_heading(render_back(node.to_tokens()).strip())

    return Ok(node.next_sibling)


def _parse_h2(
    sections: list[SectionSource], node: SyntaxTreeNode, artifact_id: FullArtifactId | None
) -> Result[SyntaxTreeNode | None, ErrorsList]:
    section = sections[-1]

    if section.title is None:
        return Err([world_errors.MarkdownH2BeforeH1Title(artifact_id=artifact_id)])

    new_section = SectionSource(
        level=SectionLevel.h2,
        title=clear_heading(render_back(node.to_tokens()).strip()),
        original_tokens=[],
        analysis_tokens=[],
        configs=[],
    )

    sections.append(new_section)

    return Ok(node.next_sibling)


def _parse_heading(
    sections: list[SectionSource], node: SyntaxTreeNode, artifact_id: FullArtifactId | None
) -> Result[SyntaxTreeNode | None, ErrorsList]:
    section = sections[-1]

    if node.tag == "h1":
        return _parse_h1(sections, node, artifact_id)

    if node.tag == "h2":
        return _parse_h2(sections, node, artifact_id)

    section.original_tokens.extend(node.to_tokens())
    return Ok(node.next_sibling)


def _parse_fence(sections: list[SectionSource], node: SyntaxTreeNode) -> SyntaxTreeNode | None:  # noqa: CCR001
    section = sections[-1]

    info_parts = node.info.split()

    format = info_parts[0] if info_parts else ""

    properties: dict[str, str | bool] = {}

    for part in info_parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            properties[key] = value
            continue

        properties[part] = True

    if "donna" in properties:
        code_block = CodeSource(
            format=format,
            properties=properties,
            content=node.content,
        )

        section.configs.append(code_block)
    else:
        section.original_tokens.extend(node.to_tokens())

    return node.next_sibling


def _parse_nested(sections: list[SectionSource], node: SyntaxTreeNode) -> SyntaxTreeNode | None:
    section = sections[-1]

    assert node.nester_tokens is not None

    section.original_tokens.append(node.nester_tokens.opening)

    return node.children[0]


def _parse_others(sections: list[SectionSource], node: SyntaxTreeNode) -> SyntaxTreeNode | None:
    section = sections[-1]

    section.original_tokens.extend(node.to_tokens())

    current: SyntaxTreeNode | None = node

    while current is not None and current.type != "root" and current.next_sibling is None:
        current = current.parent

        if current is None:
            break

        if current.type != "root":
            assert current.nester_tokens is not None
            section.original_tokens.append(current.nester_tokens.closing)

    return current


@unwrap_to_error
def parse(  # noqa: CCR001, CFQ001
    text: str, *, artifact_id: FullArtifactId | None = None
) -> Result[list[SectionSource], ErrorsList]:  # pylint: disable=R0912, R0915
    md = MarkdownIt("commonmark")  # TODO: later we may want to customize it with plugins

    tokens = md.parse(text)

    # we do not need root node
    node: SyntaxTreeNode | None = SyntaxTreeNode(tokens).children[0]

    sections: list[SectionSource] = [
        SectionSource(
            level=SectionLevel.h1,
            title=None,
            original_tokens=[],
            analysis_tokens=[],
            configs=[],
        )
    ]

    while node is not None:

        if node.type == "heading":
            node = _parse_heading(sections, node, artifact_id).unwrap()
            continue

        if node.type == "fence":
            node = _parse_fence(sections, node)
            continue

        if node.is_nested:
            node = _parse_nested(sections, node)
            continue

        node = _parse_others(sections, node)

        if node is None:
            break

        node = node.next_sibling

    return Ok(sections)

    return sections
