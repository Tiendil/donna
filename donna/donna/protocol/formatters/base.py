from donna.protocol.cells import Cell


class Formatter:

    def format_cell(self, cell: Cell) -> bytes:
        raise NotImplementedError()

    def format_cells(self, cells: list[Cell]) -> bytes:
        return b"\n".join([self.format_cell(cell) for cell in cells])
