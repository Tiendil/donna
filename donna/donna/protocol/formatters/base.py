from abc import ABC, abstractmethod

from donna.protocol.cells import Cell


class Formatter(ABC):

    @abstractmethod
    def format_cell(self, cell: Cell, single_mode: bool) -> bytes: ...  # noqa: E704

    @abstractmethod
    def format_cells(self, cells: list[Cell]) -> bytes: ...  # noqa: E704
