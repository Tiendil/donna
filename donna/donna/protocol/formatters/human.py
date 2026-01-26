from donna.protocol.cells import Cell
from donna.protocol.formatters.base import Formatter as BaseFormatter


class Formatter(BaseFormatter):

    def format_cell(self, cell: Cell) -> bytes:
        id = cell.short_id()

        lines = [f"----- DONNA CELL {id} -----"]

        for meta_key, meta_value in sorted(cell.meta.items()):
            lines.append(f"{meta_key} = {meta_value}")

        if cell.meta and cell.content:
            lines.append("")

        if cell.content:
            lines.append(cell.content.strip())

        return "\n".join(lines).encode()

    def format_cells(self, cells: list[Cell]) -> bytes:
        formatted_cells = [self.format_cell(cell) for cell in cells]
        return b"\n\n".join(formatted_cells)
