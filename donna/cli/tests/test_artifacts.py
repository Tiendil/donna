import pathlib

from donna.cli.tests import helpers


class TestList:
    def test_lists_discovered_artifacts_with_selected_protocol(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)

        result = helpers.invoke(["--config", str(config_path), "-p", "llm", "list"])

        assert result.exit_code == 0
        assert "kind=artifact_status" in result.output
        assert "artifact_id=@/workflows/test.donna.md" in result.output
        assert "artifact_title=Test Workflow" in result.output


class TestRender:
    def test_renders_raw_markdown_without_cell_wrapping(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)

        result = helpers.invoke(
            ["--config", str(config_path), "-p", "human", "render", "--mode", "view", "@/workflows/test.donna.md"]
        )

        assert result.exit_code == 0
        assert "# Test Workflow" in result.output
        assert "----- DONNA CELL" not in result.output
        assert "--DONNA-CELL" not in result.output


class TestValidate:
    def test_all_option_validates_every_discovered_artifact(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "validate", "--all"])

        assert result.exit_code == 0
        records = helpers.json_lines(result.output)
        assert records[0]["content"] == "All artifacts are valid"

    def test_explicit_artifact_argument_is_normalized(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)

        result = helpers.invoke(
            [
                "--config",
                str(config_path),
                "-p",
                "llm",
                "validate",
                "@/workflows/test.donna.md",
            ]
        )

        assert result.exit_code == 0
        assert "kind=operation_succeeded" in result.output

    def test_rejects_all_option_combined_with_artifact_argument(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)

        result = helpers.invoke(["--config", str(config_path), "validate", "--all", "@/workflows/test.donna.md"])

        assert result.exit_code == 2
        assert "Pass artifact ids or --all, not both." in result.output

    def test_rejects_missing_selection(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)

        result = helpers.invoke(["--config", str(config_path), "validate"])

        assert result.exit_code == 2
        assert "Pass artifact ids or --all." in result.output


class TestParseArtifactIdArgument:
    def test_rejects_unsupported_artifact_extension(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        (tmp_path / "workflows").mkdir()
        (tmp_path / "workflows" / "test.md").write_text("# Test\n", encoding="utf-8")

        result = helpers.invoke(["--config", str(config_path), "render", "--mode", "view", "@/workflows/test.md"])

        assert result.exit_code != 0
        assert "Unsupported artifact extension" in result.output
