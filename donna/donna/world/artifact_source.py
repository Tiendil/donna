import enum
import logging
from typing import Any

import pydantic
from markdown_it import MarkdownIt
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
from mdformat.renderer import MDRenderer

from donna.core.entities import BaseEntity

LOGGER = logging.getLogger(__name__)


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

    def debug_print(self) -> None:
        LOGGER.debug("--- Debug Code Source ---")
        LOGGER.debug("format: %s", self.format)
        LOGGER.debug("properties: %s", self.properties)
        LOGGER.debug(self.content)
        LOGGER.debug("--- End of code ---")


class SectionSource(BaseEntity):
    level: SectionLevel
    title: str | None
    tokens: list[Token]
    configs: list[CodeSource]

    model_config = pydantic.ConfigDict(frozen=False)

    def debug_print(self) -> None:
        LOGGER.debug("--- Debug Section Source ---")
        LOGGER.debug("level: %s", self.level)
        LOGGER.debug("title: %s", self.title)
        LOGGER.debug("---body---")
        LOGGER.debug(render_back(self.tokens))
        for block in self.configs:
            block.debug_print()
        LOGGER.debug("--- End of section ---")

    def as_markdown(self) -> str:
        parts = []

        if self.title is not None:
            match self.level:
                case SectionLevel.h1:
                    prefix = "#"
                case SectionLevel.h2:
                    prefix = "##"

            parts.append(f"{prefix} {self.title}")

        parts.append(render_back(self.tokens))

        return "\n".join(parts)


class ArtifactSource(BaseEntity):
    world_id: str
    id: str

    head: SectionSource
    tail: list[SectionSource]

    def as_markdown(self) -> str:
        parts = [self.head.as_markdown()]

        for section in self.tail:
            parts.append(section.as_markdown())

        return "\n".join(parts)

    def debug_print(self) -> None:
        LOGGER.debug("--- Debug Artifact Source ---")
        LOGGER.debug("world: %s", self.world_id)
        LOGGER.debug("id: %s", self.id)
        self.head.debug_print()
        for section in self.tail:
            section.debug_print()


def render_back(tokens: list[Token]) -> str:
    renderer = MDRenderer()
    return renderer.render(tokens, {}, {})


def clear_heading(text: str) -> str:
    return text.lstrip("#").strip()


def parse_markdown(text: str) -> list[SectionSource]:  # noqa: CCR001 # pylint: disable=R0912, R0915
    md = MarkdownIt("commonmark")  # TODO: later we may want to customize it with plugins

    tokens = md.parse(text)

    try:
        # we do not need root node
        node: SyntaxTreeNode | None = SyntaxTreeNode(tokens).children[0]
    except Exception as e:
        raise NotImplementedError("Failed to parse markdown") from e

    sections: list[SectionSource] = [
        SectionSource(
            level=SectionLevel.h1,
            title=None,
            tokens=[],
            configs=[],
        )
    ]

    while node is not None:
        section = sections[-1]

        if node.type == "heading":
            if node.tag == "h1":
                if section.level != SectionLevel.h1:
                    raise NotImplementedError("Multiple H1 sections are not supported")

                if section.title is not None:
                    raise NotImplementedError("Multiple H1 titles are not supported")

                section.title = clear_heading(render_back(node.to_tokens()).strip())

                node = node.next_sibling
                continue

            if node.tag == "h2":
                if section.title is None:
                    raise NotImplementedError("H2 section found before H1 title")

                new_section = SectionSource(
                    level=SectionLevel.h2,
                    title=clear_heading(render_back(node.to_tokens()).strip()),
                    tokens=[],
                    configs=[],
                )

                sections.append(new_section)

                node = node.next_sibling
                continue

            section.tokens.extend(node.to_tokens())
            node = node.next_sibling
            continue

        if node.type == "fence":
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
                section.tokens.extend(node.to_tokens())

            node = node.next_sibling
            continue

        if node.is_nested:
            assert node.nester_tokens is not None
            section.tokens.append(node.nester_tokens.opening)
            node = node.children[0]
            continue

        section.tokens.extend(node.to_tokens())

        while node is not None and node.type != "root" and node.next_sibling is None:
            node = node.parent

            if node is None:
                break

            if node.type != "root":
                assert node.nester_tokens is not None
                section.tokens.append(node.nester_tokens.closing)

        if node is None:
            break

        node = node.next_sibling

    return sections


def parse_artifact(world_id: str, id: str, text: str) -> ArtifactSource:
    sections = parse_markdown(text)

    if not sections:
        raise NotImplementedError("Artifact must have at least one section")

    head = sections[0]
    tail = sections[1:]

    artifact = ArtifactSource(
        world_id=world_id,
        id=id,
        head=head,
        tail=tail,
    )

    return artifact
