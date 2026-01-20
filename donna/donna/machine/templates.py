from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.core.entities import BaseEntity
from donna.domain.ids import DirectiveKindId


class DirectiveKind(BaseEntity):
    id: DirectiveKindId
    name: str
    description: str
    example: str

    @jinja2.pass_context
    def __call__(self, context: Context, *argv: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("You MUST implement this method.")
