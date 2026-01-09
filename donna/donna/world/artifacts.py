import enum
import logging
from typing import Any

import pydantic
from markdown_it import MarkdownIt
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
from mdformat.renderer import MDRenderer

from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactId
from donna.world import markdown


def parse_artifact(full_id: FullArtifactId, text: str) -> markdown.ArtifactSource:
    sections = markdown.parse(text)

    if not sections:
        raise NotImplementedError("Artifact must have at least one section")

    head = sections[0]
    tail = sections[1:]

    artifact = markdown.ArtifactSource(
        id=full_id,
        head=head,
        tail=tail,
    )

    return artifact
