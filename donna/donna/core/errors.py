import pydantic

from donna.core.entities import BaseEntity
from donna.protocol.cells import Cell, MetaValue, to_meta_value


class EnvironmentError(BaseEntity):
    cell_kind: str
    cell_media_type: str = "text/markdown"

    code: str
    message: str
    ways_to_fix: list[str] = pydantic.Field(default_factory=list)

    def meta(self) -> dict[str, MetaValue]:
        meta: dict[str, MetaValue] = {
            "error_code": self.code,
        }

        for field_name, _field in self.model_fields.items():
            if field_name in ("code", "message", "cell_kind"):
                continue

            value = getattr(self, field_name)

            if value is None:
                continue

            meta[field_name] = to_meta_value(value)

        return meta

    def content_intro(self) -> str:
        return "Error"

    def content(self) -> str:
        intro = self.content_intro()

        message = self.message.format(error=self).strip()

        if "\n" in self.message:
            content = f"{intro}:\n\n{message}"
        else:
            content = f"{intro}: {message}"

        if not self.ways_to_fix:
            return content

        if len(self.ways_to_fix) == 1:
            return f"{content}\nWay to fix: {self.ways_to_fix[0]}"

        fixes = "\n".join(f"- {fix}" for fix in self.ways_to_fix)

        return f"{content}\n\nWays to fix:\n\n{fixes}"

    def cell(self) -> Cell:
        return Cell.build(
            kind=self.cell_kind,
            media_type=self.cell_media_type,
            content=self.content(),
            **self.meta(),
        )


ErrorsList = list[EnvironmentError]
