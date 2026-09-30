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
    def test_home_relative_artifact_argument(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_path = helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))

        result = helpers.invoke(
            ["--config", str(config_path), "render", "--mode", "view", "~/workflows/test.donna.md"]
        )

        assert result.exit_code == 0
        assert "# Test Workflow" in result.stdout

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
    @pytest.mark.parametrize("all_artifacts", [False, True])
    def test_collected_errors__are_journaled_and_reported(self, tmp_path: pathlib.Path, all_artifacts: bool) -> None:
        config_path = helpers.write_config(tmp_path)
        artifact_ids = ["@/workflows/first.donna.md", "@/workflows/second.donna.md"]
        for artifact_id in artifact_ids:
            workflow_path = helpers.write_workflow(tmp_path, path=artifact_id.removeprefix("@/"))
            workflow_path.write_text(
                workflow_path.read_text(encoding="utf-8").replace(
                    'start_operation_id = "finish"', 'start_operation_id = "missing"'
                ),
                encoding="utf-8",
            )
        initialized = helpers.invoke(["--config", str(config_path), "-p", "automation", "new-session"])
        assert initialized.exit_code == 0
        selection = ["--all"] if all_artifacts else artifact_ids

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "validate", *selection])

        assert result.exit_code == 3
        assert not result.stderr
        records = helpers.json_lines(result.stdout)
        diagnostics = [record for record in records if record.get("type") == "error"]
        journal = [record for record in records if record.get("actor_id") == "donna"]
        assert [
            record["artifact_id"]
            for record in diagnostics
            if record["code"] == "donna.workflows.wrong_start_operation"
        ] == artifact_ids
        assert len(journal) == len(diagnostics)
        for entry, diagnostic in zip(journal, diagnostics, strict=True):
            assert str(entry["message"]).startswith("Error: ")
            assert str(entry["message"]).endswith(f"[{diagnostic['code']}]")
        assert not any(record.get("type") == "operation_succeeded" for record in records)

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize("selection", [["--all"], ["@/workflows/test.donna.md"]])
    def test_invalid_workflow__uses_shared_error_exit_code(
        self, tmp_path: pathlib.Path, protocol: str, selection: list[str]
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        workflow_path = helpers.write_workflow(tmp_path)
        workflow_path.write_text(
            workflow_path.read_text(encoding="utf-8").replace(
                'start_operation_id = "finish"', 'start_operation_id = "missing"'
            ),
            encoding="utf-8",
        )

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "validate", *selection])

        assert result.exit_code == 3
        if protocol == "automation":
            assert not result.stderr
            records = helpers.json_lines(result.stdout)
            assert any(record.get("type") == "error" for record in records)
            assert not any(record.get("type") == "operation_succeeded" for record in records)
        else:
            separator = " = " if protocol == "human" else "="
            assert f"kind{separator}error\n" in result.stderr
            assert f"kind{separator}error\n" not in result.stdout
            assert f"kind{separator}operation_succeeded\n" not in result.stdout

    def test_all_option_validates_every_discovered_artifact(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "validate", "--all"])

        assert result.exit_code == 0
        records = helpers.json_lines(result.output)
        assert records[0]["content"] == "All artifacts are valid"
        assert records[0]["type"] == "operation_succeeded"

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
        assert "type=operation_succeeded" in result.output

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
    def test_target_resolution_failure_uses_shared_diagnostic(self, tmp_path: pathlib.Path, protocol: str) -> None:
        config_path = helpers.write_config(tmp_path)
        link = tmp_path / "loop"
        link.symlink_to(link)
        target = link / "workflow.donna.md"

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "validate", str(target)])

        assert result.exit_code == 3
        if protocol == "automation":
            records = helpers.json_lines(result.stdout)
            diagnostics = [record for record in records if record.get("code") == "path_resolution_failed"]
            assert len(diagnostics) == 1
            assert diagnostics[0]["path"] == str(target)
            assert diagnostics[0]["reason"]
            assert "cause" not in diagnostics[0]
            assert not result.stderr
        else:
            assert str(target) in result.stderr

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_root_resolution_failure_uses_shared_diagnostic(
        self, tmp_path: pathlib.Path, mocker: MockerFixture, protocol: str
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        root = tmp_path / "loop"
        root.symlink_to(root)
        failure = resolve_project_root(root)
        mocker.patch("llm_tool_cli.paths.filesystem.resolve_project_root", return_value=failure)

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "validate", "@/workflow.donna.md"])

        assert result.exit_code == 3
        error = failure.unwrap_err()[0]
        if protocol == "automation":
            records = helpers.json_lines(result.stdout)
            helpers.assert_error_cells(
                [record for record in records if record.get("code") == "path_resolution_failed"], [error]
            )
            assert not result.stderr
        else:
            assert error.format_message() in result.stderr

    @pytest.mark.parametrize("command", [["render", "--mode", "view"], ["validate"], ["run"]])
    def test_invalid_path_uses_shared_automation_diagnostic(self, tmp_path: pathlib.Path, command: list[str]) -> None:
        config_path = helpers.write_config(tmp_path)
        value = "@/../outside.donna.md"

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", *command, value])

        assert result.exit_code == 3
        records = helpers.json_lines(result.stdout)
        diagnostic = [record for record in records if record.get("code") == "invalid_project_path"]
        helpers.assert_error_cells(diagnostic, [InvalidProjectPath(path=value)])
        assert result.stderr == ""

    @pytest.mark.parametrize("protocol", ["human", "llm"])
    def test_invalid_path_uses_shared_stderr_diagnostic(self, tmp_path: pathlib.Path, protocol: str) -> None:
        config_path = helpers.write_config(tmp_path)
        value = "@/workflows//test.donna.md"

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "validate", value])

        assert result.exit_code == 3
        assert InvalidProjectPath(path=value).format_message() in result.stderr
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
        helpers.assert_error_cells(
            [record for record in records if record.get("code") == "invalid_project_path"],
            [InvalidProjectPath(path=value)],
        )

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

        assert result.exit_code == 3
        records = helpers.json_lines(result.stdout)
        assert any(record.get("code") == "donna.domain.invalid_id_format" for record in records)
