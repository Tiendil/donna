import pathlib

import pytest
from llm_tool_cli.paths import resolve_project_root
from llm_tool_cli.paths.errors import InvalidProjectPath
from pytest_mock import MockerFixture

from donna.cli.tests import helpers
from donna.domain.internal_ids import ActionRequestId


class TestList:
    def test_config_home_marker__loads_project_in_home(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)
        mocker.patch.dict("os.environ", {"HOME": str(tmp_path)})

        result = helpers.invoke(["--config", "~/donna.toml", "-p", "automation", "list"])

        assert result.exit_code == 0
        records = helpers.json_lines(result.stdout)
        assert any(record.get("artifact_id") == "@/workflows/test.donna.md" for record in records)

    def test_lists_discovered_artifacts_with_selected_protocol(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)

        result = helpers.invoke(["--config", str(config_path), "-p", "llm", "list"])

        assert result.exit_code == 0
        assert "kind=artifact_status" in result.output
        assert "artifact_id=@/workflows/test.donna.md" in result.output
        assert "artifact_title=Test Workflow" in result.output


class TestRender:
    def test_config_home_marker__uses_resolved_project_for_artifact_paths(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)
        mocker.patch.dict("os.environ", {"HOME": str(tmp_path)})

        result = helpers.invoke(["--config", "~/donna.toml", "render", "--mode", "view", "@/workflows/test.donna.md"])

        assert result.exit_code == 0
        assert "# Test Workflow" in result.stdout

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
    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_root_resolution_failure_uses_shared_diagnostic(
        self, tmp_path: pathlib.Path, mocker: MockerFixture, protocol: str
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        root = tmp_path / "loop"
        root.symlink_to(root)
        failure = resolve_project_root(root)
        mocker.patch("donna.workspaces.paths.resolve_project_root", return_value=failure)

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "validate", "@/workflow.donna.md"])

        assert result.exit_code == 3
        error = failure.unwrap_err()[0]
        if protocol == "automation":
            records = helpers.json_lines(result.stdout)
            assert [record for record in records if record.get("code") == "path_resolution_failed"] == [
                error.as_record()
            ]
            assert not result.stderr
        else:
            assert result.stderr == error.format_message() + "\n"

    @pytest.mark.parametrize("command", [["render", "--mode", "view"], ["validate"], ["run"]])
    def test_invalid_path_uses_shared_automation_diagnostic(self, tmp_path: pathlib.Path, command: list[str]) -> None:
        config_path = helpers.write_config(tmp_path)
        value = "@/../outside.donna.md"

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", *command, value])

        assert result.exit_code == 3
        records = helpers.json_lines(result.stdout)
        diagnostic = [record for record in records if record.get("code") == "invalid_project_path"]
        assert diagnostic == [InvalidProjectPath(path=value).as_record()]
        assert result.stderr == ""

    @pytest.mark.parametrize("protocol", ["human", "llm"])
    def test_invalid_path_uses_shared_stderr_diagnostic(self, tmp_path: pathlib.Path, protocol: str) -> None:
        config_path = helpers.write_config(tmp_path)
        value = "@/workflows//test.donna.md"

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "validate", value])

        assert result.exit_code == 3
        assert result.stderr == InvalidProjectPath(path=value).format_message() + "\n"
        assert "kind=domain_error" not in result.stdout

    def test_rejects_unsupported_artifact_extension(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        (tmp_path / "workflows").mkdir()
        (tmp_path / "workflows" / "test.md").write_text("# Test\n", encoding="utf-8")

        result = helpers.invoke(["--config", str(config_path), "render", "--mode", "view", "@/workflows/test.md"])

        assert result.exit_code != 0
        assert "Unsupported artifact extension" in result.output


class TestParseArtifactSectionIdArgument:
    def test_invalid_artifact_path_uses_shared_diagnostic(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        value = "@/../workflow.donna.md"

        result = helpers.invoke(
            [
                "--config",
                str(config_path),
                "-p",
                "automation",
                "complete-action-request",
                str(ActionRequestId.build("AR", 1)),
                value + ":finish",
            ]
        )

        assert result.exit_code == 3
        records = helpers.json_lines(result.stdout)
        assert [record for record in records if record.get("code") == "invalid_project_path"] == [
            InvalidProjectPath(path=value).as_record()
        ]

    def test_invalid_section_retains_domain_diagnostic(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)

        result = helpers.invoke(
            [
                "--config",
                str(config_path),
                "-p",
                "automation",
                "complete-action-request",
                str(ActionRequestId.build("AR", 1)),
                "@/workflow.donna.md:---",
            ]
        )

        assert result.exit_code == 0
        records = helpers.json_lines(result.stdout)
        assert any(record.get("error_code") == "donna.domain.invalid_id_format" for record in records)
