import json

from donna.protocol.cells import Cell
from donna.protocol.formatters.base import Formatter as BaseFormatter


class Formatter(BaseFormatter):

    def format_cell(self, cell: Cell, single_mode: bool) -> bytes:
        data: dict[str, str | int | bool | None] = {"id": cell.short_id()}

        for meta_key, meta_value in sorted(cell.meta.items()):
            data[meta_key] = meta_value

        data["content"] = cell.content.strip() if cell.content else None

        return json.dumps(data, ensure_ascii=False, indent=None, separators=(",", ":"), sort_keys=True).encode()

    def format_cells(self, cells: list[Cell]) -> bytes:
        single_mode = (len(cells) == 1)
        formatted_cells = [self.format_cell(cell, single_mode=single_mode) for cell in cells]
        return b"\n".join(formatted_cells)
