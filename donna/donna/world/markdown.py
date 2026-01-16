import enum
from typing import Any

import pydantic
from markdown_it import MarkdownIt
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
from mdformat.renderer import MDRenderer

from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactId


class SectionLevel(str, enum.Enum):
    h1 = "h1"
    h2 = "h2"


class CodeSource(BaseEntity):
    format: str
    properties: dict[str, str | bool]
    content: str

    def structured_data(self) -> Any:
        if self.format == "json":
            import json

            return json.loads(self.content)

        if self.format == "yaml" or self.format == "yml":
            import yaml

            return yaml.safe_load(self.content)

        if self.format == "toml":
            import tomllib

            return tomllib.loads(self.content)

        raise NotImplementedError(f"Unsupported code format: {self.format}")


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

    def merged_configs(self) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for config in self.configs:
            result.update(config.structured_data())

        return result


# TODO: we may want to move artifact source definition to world.artifacts
class ArtifactSource(BaseEntity):
    id: FullArtifactId

    head: SectionSource
    tail: list[SectionSource]

    def as_original_markdown(self) -> str:
        parts = [self.head.as_original_markdown(with_title=True)]

        for section in self.tail:
            parts.append(section.as_original_markdown(with_title=True))

        return "\n".join(parts)

    def as_analysis_markdown(self) -> str:
        parts = [self.head.as_analysis_markdown(with_title=True)]

        for section in self.tail:
            parts.append(section.as_analysis_markdown(with_title=True))

        return "\n".join(parts)


def render_back(tokens: list[Token]) -> str:
    renderer = MDRenderer()
    return renderer.render(tokens, {}, {})


def clear_heading(text: str) -> str:
    return text.lstrip("#").strip()


def _parse_h1(sections: list[SectionSource], node: SyntaxTreeNode) -> SyntaxTreeNode | None:
    section = sections[-1]

    if section.level != SectionLevel.h1:
        raise NotImplementedError("Multiple H1 sections are not supported")

    if section.title is not None:
        raise NotImplementedError("Multiple H1 titles are not supported")

    section.title = clear_heading(render_back(node.to_tokens()).strip())

    return node.next_sibling


def _parse_h2(sections: list[SectionSource], node: SyntaxTreeNode) -> SyntaxTreeNode | None:
    section = sections[-1]

    if section.title is None:
        raise NotImplementedError("H2 section found before H1 title")

    new_section = SectionSource(
        level=SectionLevel.h2,
        title=clear_heading(render_back(node.to_tokens()).strip()),
        original_tokens=[],
        analysis_tokens=[],
        configs=[],
    )

    sections.append(new_section)

    return node.next_sibling


def _parse_heading(sections: list[SectionSource], node: SyntaxTreeNode) -> SyntaxTreeNode | None:
    section = sections[-1]

    if node.tag == "h1":
        return _parse_h1(sections, node)

    if node.tag == "h2":
        return _parse_h2(sections, node)

    section.original_tokens.extend(node.to_tokens())
    return node.next_sibling


def _parse_fence(sections: list[SectionSource], node: SyntaxTreeNode) -> SyntaxTreeNode | None:
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


def parse(text: str) -> list[SectionSource]:  # noqa: CCR001, CFQ001 # pylint: disable=R0912, R0915
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
            node = _parse_heading(sections, node)
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

    return sections
