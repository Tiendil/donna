from donna.protocol.cells import Cell


class Formatter:

    def format_cell(self, cell: Cell, single_mode: bool) -> bytes:
        raise NotImplementedError()

    def format_cells(self, cells: list[Cell]) -> bytes:
        raise NotImplementedError()
