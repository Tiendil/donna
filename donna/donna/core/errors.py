
from donna.core.entities import BaseEntity
from donna.protocol.cells import Cell, MetaValue, to_meta_value


class EnvironmentError(BaseEntity):
    cell_kind: str
    cell_media_type: str = "text/markdown"

    code: str
    message: str

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
            return f"{intro}:\n\n{message}"

        return f"{intro}: {message}"

    def cell(self) -> Cell:
        return Cell.build(
            kind=self.cell_kind,
            media_type=self.cell_media_type,
            content=self.content(),
            **self.meta(),
        )
