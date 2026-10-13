import json
import pathlib

import pytest
from llm_tool_cli.paths import resolve_project_root
from llm_tool_cli.paths.errors import InvalidProjectPath
from llm_tool_cli.protocol.tests.helpers import assert_error_cells, cell_payloads
from pytest_mock import MockerFixture

from donna.cli.tests import helpers
from donna.domain.internal_ids import ActionRequestId


class TestList:
    def test_skips_linked_workflows(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)
        (tmp_path / "workflows/linked.donna.md").symlink_to(tmp_path / "workflows/test.donna.md")
        (tmp_path / "workflows/cycle").symlink_to(tmp_path / "workflows")

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "list"])

        assert result.exit_code == 0
        assert [r["artifact_id"] for r in helpers.json_lines(result.stdout) if "artifact_id" in r] == [
            "@/workflows/test.donna.md"
        ]

    def test_rejects_linked_workflow_directory(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        (tmp_path / "workflows").symlink_to(tmp_path)

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "list"])

        assert result.exit_code == 3
        assert any(r.get("code") == "invalid_project_path" for r in helpers.json_lines(result.stdout))

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

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize("mode", ["view", "execute", "analysis"])
    @pytest.mark.parametrize("with_session", [False, True])
    def test_renders_markdown_as_protocol_cell(  # noqa: CCR001
        self, tmp_path: pathlib.Path, protocol: str, mode: str, with_session: bool
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        template = "{{ 'Expanded café 日本語' }}"
        workflow_path = helpers.write_workflow(tmp_path, description=template)
        expected = workflow_path.read_text(encoding="utf-8").replace(template, "Expanded café 日本語").strip()
        if with_session:
            initialized = helpers.invoke(["--config", str(config_path), "-p", "automation", "new-session"])
            assert initialized.exit_code == 0, initialized.exception

        result = helpers.invoke(
            ["--config", str(config_path), "-p", protocol, "render", "--mode", mode, "@/workflows/test.donna.md"]
        )

        assert result.exit_code == 0, result.exception
        assert not result.stderr
        if protocol == "automation":
            records = [json.loads(line) for line in result.stdout.splitlines()]
            assert len(records) == 2
            assert cell_payloads(records[-1:]) == [{"type": "rendered_artifact", "content": expected}]
            assert records[0]["message"] == f"Render artifact `@/workflows/test.donna.md` in `{mode}` mode"
            assert records[0]["current_task_id"] is None
        else:
            separator = " = " if protocol == "human" else "="
            prefix = "----- DONNA CELL " if protocol == "human" else "--DONNA-CELL "
            assert prefix in result.stdout
            assert f"kind{separator}rendered_artifact\n" in result.stdout
            assert f"media_type{separator}text/markdown\n" in result.stdout
            assert f"type{separator}rendered_artifact\n" in result.stdout
            assert expected in result.stdout
        assert (tmp_path / ".session" / "donna" / "state.json").is_file() == with_session


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
            assert f"kind{separator}error\n" in result.stdout
            assert not result.stderr
            assert f"kind{separator}operation_succeeded\n" not in result.stdout

    def test_all_option_validates_every_discovered_artifact(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "validate", "--all"])

        assert result.exit_code == 0
        records = helpers.json_lines(result.output)
        assert records[-1]["content"] == "All artifacts are valid"
        assert records[-1]["type"] == "operation_succeeded"

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
    @pytest.mark.parametrize("spelling", ["identifier", "absolute", "relative"])
    def test_rejects_internal_link_for_all_input_spellings(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, spelling: str
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        helpers.write_workflow(tmp_path)
        link = tmp_path / "workflows/linked.donna.md"
        link.symlink_to(tmp_path / "workflows/test.donna.md")
        monkeypatch.chdir(tmp_path)
        value = {
            "identifier": "@/workflows/linked.donna.md",
            "relative": "workflows/linked.donna.md",
            "absolute": str(link),
        }[spelling]

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "validate", value])

        assert result.exit_code == 3
        assert_error_cells(
            [r for r in helpers.json_lines(result.stdout) if r.get("type") == "error"],
            [InvalidProjectPath(path=str(link))],
        )

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_target_symlink_loop_uses_invalid_path_diagnostic(self, tmp_path: pathlib.Path, protocol: str) -> None:
        config_path = helpers.write_config(tmp_path)
        link = tmp_path / "loop"
        link.symlink_to(link)
        target = link / "workflow.donna.md"

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "validate", str(target)])

        assert result.exit_code == 3
        if protocol == "automation":
            records = helpers.json_lines(result.stdout)
            diagnostics = [record for record in records if record.get("code") == "invalid_project_path"]
            assert len(diagnostics) == 1
            assert diagnostics[0]["path"] == str(target)
            assert "cause" not in diagnostics[0]
            assert not result.stderr
        else:
            assert str(target) in result.stdout

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
            assert_error_cells(
                [record for record in records if record.get("code") == "path_resolution_failed"], [error]
            )
            assert not result.stderr
        else:
            assert error.format_message() in result.stdout

    @pytest.mark.parametrize("command", [["render", "--mode", "view"], ["validate"], ["run"]])
    def test_invalid_path_uses_shared_automation_diagnostic(self, tmp_path: pathlib.Path, command: list[str]) -> None:
        config_path = helpers.write_config(tmp_path)
        value = "@/../outside.donna.md"

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", *command, value])

        assert result.exit_code == 3
        records = helpers.json_lines(result.stdout)
        diagnostic = [record for record in records if record.get("code") == "invalid_project_path"]
        assert_error_cells(diagnostic, [InvalidProjectPath(path=value)])
        assert result.stderr == ""

    @pytest.mark.parametrize("protocol", ["human", "llm"])
    def test_invalid_path_uses_shared_stdout_diagnostic(self, tmp_path: pathlib.Path, protocol: str) -> None:
        config_path = helpers.write_config(tmp_path)
        value = "@/workflows//test.donna.md"

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "validate", value])

        assert result.exit_code == 3
        assert InvalidProjectPath(path=value).format_message() in result.stdout
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
        assert_error_cells(
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
