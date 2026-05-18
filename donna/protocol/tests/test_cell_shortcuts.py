from donna.protocol import cell_shortcuts


class TestOperationSucceeded:
    def test_creates_markdown_operation_succeeded_cell(self) -> None:
        cell = cell_shortcuts.operation_succeeded("Done.", operation="setup")

        assert cell.kind == "operation_succeeded"
        assert cell.media_type == "text/markdown"
        assert cell.content == "Done."
        assert cell.meta == {"operation": "setup"}


class TestOperationFailed:
    def test_creates_markdown_operation_failed_cell(self) -> None:
        cell = cell_shortcuts.operation_failed("Failed.", operation="setup")

        assert cell.kind == "operation_failed"
        assert cell.media_type == "text/markdown"
        assert cell.content == "Failed."
        assert cell.meta == {"operation": "setup"}


class TestInfo:
    def test_creates_markdown_info_cell(self) -> None:
        cell = cell_shortcuts.info("Ready.", scope="workspace")

        assert cell.kind == "info"
        assert cell.media_type == "text/markdown"
        assert cell.content == "Ready."
        assert cell.meta == {"scope": "workspace"}
