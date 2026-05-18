from donna.protocol.cells import Cell
from donna.protocol.nodes import Node


class _SampleNode(Node):
    __slots__ = ("_name", "_references")

    def __init__(self, name: str, references: list[Node] | None = None) -> None:
        self._name = name
        self._references = references or []

    def status(self) -> Cell:
        return Cell.build_markdown(kind="node_status", content=f"Status {self._name}")

    def info(self) -> Cell:
        return Cell.build_markdown(kind="node_info", content=f"Info {self._name}")

    def references(self) -> list[Node]:
        return self._references


class _StatusOnlyNode(Node):
    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        self._name = name

    def status(self) -> Cell:
        return Cell.build_markdown(kind="node_status", content=f"Status {self._name}")


class TestNode:
    def test_info__defaults_to_status(self) -> None:
        node = _StatusOnlyNode("root")

        info = node.info()

        assert info.kind == "node_status"
        assert info.content == "Status root"

    def test_details__includes_info_for_node_and_references(self) -> None:
        reference = _SampleNode("reference")
        node = _SampleNode("root", references=[reference])

        assert [cell.content for cell in node.details()] == ["Info root", "Info reference"]

    def test_index__includes_status_for_node_and_references(self) -> None:
        reference = _SampleNode("reference")
        node = _SampleNode("root", references=[reference])

        assert [cell.content for cell in node.index()] == ["Status root", "Status reference"]

    def test_references__defaults_to_empty_list(self) -> None:
        assert _StatusOnlyNode("root").references() == []

    def test_components__defaults_to_empty_list(self) -> None:
        assert _StatusOnlyNode("root").components() == []
