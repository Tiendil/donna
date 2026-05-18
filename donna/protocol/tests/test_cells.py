import uuid

import pytest

from donna.protocol.cells import Cell, to_meta_value
from donna.protocol.errors import ContentWithoutMediaType


class TestToMetaValue:
    @pytest.mark.parametrize(
        ("value", "expected"),
        (
            ("value", "value"),
            (1, 1),
            (True, True),
            (None, None),
            (uuid.UUID("12345678-1234-5678-9234-567812345678"), "12345678-1234-5678-9234-567812345678"),
        ),
    )
    def test_converts_supported_metadata_values(self, value: object, expected: str | int | bool | None) -> None:
        assert to_meta_value(value) == expected


class TestCell:
    def test_build__requires_media_type_when_content_is_present(self) -> None:
        with pytest.raises(ContentWithoutMediaType):
            Cell.build(kind="status", media_type=None, content="content")

    def test_build__stores_metadata_as_cell_metadata(self) -> None:
        cell = Cell.build(kind="status", media_type="text/plain", content="content", count=2, label="ready")

        assert cell.kind == "status"
        assert cell.media_type == "text/plain"
        assert cell.content == "content"
        assert cell.meta == {"count": 2, "label": "ready"}

    def test_build_meta__creates_contentless_cell(self) -> None:
        cell = Cell.build_meta(kind="status", count=0)

        assert cell.kind == "status"
        assert cell.media_type is None
        assert cell.content is None
        assert cell.meta == {"count": 0}

    def test_build_markdown__uses_markdown_media_type(self) -> None:
        cell = Cell.build_markdown(kind="status", content="# Done", count=1)

        assert cell.kind == "status"
        assert cell.media_type == "text/markdown"
        assert cell.content == "# Done"
        assert cell.meta == {"count": 1}

    def test_short_id__returns_unpadded_urlsafe_base64_id(self) -> None:
        cell = Cell.build_meta(kind="status").replace(id=uuid.UUID("12345678-1234-5678-9234-567812345678"))

        assert cell.short_id == "EjRWeBI0VniSNFZ4EjRWeA"
