
from donna.protocol.cells import Cell


class Formatter:

    def format_cell(self, cell: Cell) -> bytes:
        raise NotImplementedError()
