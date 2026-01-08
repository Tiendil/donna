import enum
import pathlib
import pydantic
from markdown_it import MarkdownIt
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode


from donna.core.entities import BaseEntity


class SectionLevel(str, enum.Enum):
    h1 = "h1"
    h2 = "h2"


class CodeSource(BaseEntity):
    format: str
    properties: dict[str, str | bool]
    content: str


class SectionSource(BaseEntity):
    level: SectionLevel
    title: str | None
    tokens: list[Token]
    configs: list[CodeSource]

    model_config = pydantic.ConfigDict(frozen=False)


class ArtifactSource(BaseEntity):
    world_id: str
    id: str

    head: SectionSource
    tail: list[SectionSource]


def parse_markdown(text: str) -> list[SectionSource]:
    md = MarkdownIt("commonmark")  # TODO: later we may want to customize it with plugins

    tokens = md.parse(text)

    try:
        node = SyntaxTreeNode(tokens, create_root=False)
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

                section.title = node.children[1].content

                node = node.next_sibling
                continue

            if node.tag == "h2":
                if section.title is None:
                    raise NotImplementedError("H2 section found before H1 title")

                new_section = SectionSource(
                    level=SectionLevel.h2,
                    title=node.children[1].content,
                    tokens=[],
                    configs=[],
                )

                sections.append(new_section)

                node = node.next_sibling
                continue

            section.tokens.extend(node.to_tokens())
            continue

        if node.type == "fence":
            info_parts = node.info.split()

            format = info_parts[0] if info_parts else ""

            properties: dict[str, str] = {}

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
            section.tokens.append(node.nester_tokens.opening)
            node = node.children[0]
            continue

        section.tokens.extend(node.to_tokens())

        while node is not None and node.next_sibling is None:
            node = node.parent
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
