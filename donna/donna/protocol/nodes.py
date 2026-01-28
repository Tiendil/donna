from donna.protocol.cells import Cell


class Node:
    """Node of Donna's knowledge graph.

    The concept of knowledge graph is highly experimental and subject to change.

    Its primary purpose is to simplify navigation through different Donna's entities
    and to provide a unified interface for retrieving information about them.

    There are two types of child nodes:

    - References — nodes that are referenced by this artifact, but not a part of it.
                   An artifact does not include information from referenced nodes
                   in its info.
                   An artifact include references in its details and index.
    - Components — nodes that are inseparable parts of this artifact.
                   An artifact includes information from them in its info.
                   An artifact does not include components in its details and index,
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
        cells.extend(child.info() for child in self.references())

        return cells

    def index(self) -> list[Cell]:
        """Returns status of itself and all its children."""
        cells = [self.status()]
        cells.extend(child.status() for child in self.references())

        return cells

    def references(self) -> list["Node"]:
        """Return all nodes that are referenced by this one"""
        return []

    def components(self) -> list["Node"]:
        """Return all nodes that are iseparable parts of this one."""
        return []
