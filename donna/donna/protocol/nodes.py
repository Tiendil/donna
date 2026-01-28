from donna.protocol.cells import Cell


class Node:
    """Node of Donna's knowledge graph.

    The concept of knowledge graph is highly experimental and subject to change.

    Its primary purpose is to simplify navigation through different Donna's entities
    and to provide a unified interface for retrieving information about them.
    """

    __slots__ = ()

    def status(self) -> Cell:
        """Returns short info about only this node."""
        raise NotImplementedError()

    def info(self) -> Cell:
        """Returns full info about only this node."""
        return self.status()

    def details(self) -> list[Cell]:
        """Returns info about the node and its children.

        The node decides itself which children to include with what level of detail.
        """
        cells = [self.info()]
        cells.extend(child.info() for child in self.children())

        return cells

    def index(self) -> list[Cell]:
        """Returns status of itself and all its children."""
        cells = [self.status()]
        cells.extend(child.status() for child in self.children())

        return cells

    def children(self) -> list["Node"]:
        """Return all child nodes."""
        return []
