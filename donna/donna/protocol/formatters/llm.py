

from donna.protocol.cells import Cell


class Formatter:

    def format_cell(self, cell: Cell) -> bytes:
        id = cell.short_id()

        lines = [f"--DONNA-CELL {id} BEGIN--"]

        for meta_key, meta_value in sorted(cell.meta.items()):
            lines.append(f"{meta_key}={meta_value}")

        if cell.meta and cell.content:
            lines.append("")

        if cell.content:
            lines.append(cell.content.strip())

        lines.append(f"--DONNA-CELL {id} END--")

        return "\n".join(lines).strip().encode()

    def format_cells(self, cells: list[Cell]) -> bytes:
        formatted_cells = [self.format_cell(cell) for cell in cells]
        return "\n".join(formatted_cells).encode()
