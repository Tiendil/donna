import jinja2

from typing import Any

from donna.core.entities import BaseEntity


class RendererKind(BaseEntity):
    id: str
    name: str
    description: str
    example: str

    @jinja2.pass_context
    def __call__(self, context, *argv, **kwargs) -> Any:
        raise NotImplementedError("You MUST implement this method.")
