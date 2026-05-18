from pathlib import Path

from pytest_mock import MockerFixture

from donna.machine.changes import ChangeAddWorkUnit, ChangeSetTaskContext
from donna.machine.tests import make as machine_make
from donna.primitives.sections import run_script
from donna.primitives.sections.run_script import (
    RunScript,
    RunScriptConfig,
    RunScriptGotoOnCodeIncludesZero,
    RunScriptInvalidExitCode,
    RunScriptMeta,
    RunScriptMissingGotoOnFailure,
    RunScriptMissingGotoOnSuccess,
    RunScriptMissingScriptBlock,
    _coerce_output,
)
from donna.primitives.tests import make
from donna.workspaces.tests import make as workspace_make


class TestRunScriptMeta:
    def test_select_next_operation__uses_success_transition_for_zero_exit_code(self) -> None:
        meta = RunScriptMeta(
            allowed_transtions={make.section_id("next"), make.section_id("done")},
            goto_on_success=make.section_id("next"),
            goto_on_failure=make.section_id("done"),
        )

        assert meta.select_next_operation(0) == make.section_id("next")

    def test_select_next_operation__uses_exit_code_specific_transition(self) -> None:
        meta = RunScriptMeta(
            allowed_transtions={make.section_id("next"), make.section_id("done")},
            goto_on_success=make.section_id("next"),
            goto_on_failure=make.section_id("done"),
            goto_on_code={"2": make.section_id("other")},
        )

        assert meta.select_next_operation(2) == make.section_id("other")

    def test_select_next_operation__falls_back_to_failure_transition(self) -> None:
        meta = RunScriptMeta(
            allowed_transtions={make.section_id("next"), make.section_id("done")},
            goto_on_success=make.section_id("next"),
            goto_on_failure=make.section_id("done"),
        )

        assert meta.select_next_operation(1) == make.section_id("done")


class TestRunScript:
    def test_markdown_construct_meta__builds_script_meta_and_allowed_transitions(self) -> None:
        source = workspace_make.section_source(
            configs=[
                workspace_make.code_source(
                    "bash",
                    "echo ok",
                    donna=True,
                    script=True,
                )
            ]
        )

        result = RunScript().markdown_construct_meta(
            artifact_id=machine_make.ARTIFACT_ID,
            source=source,
            section_config=RunScriptConfig(
                id=make.section_id("start"),
                kind=make.primitive_kind("donna.primitives.sections.run_script.RunScript"),
                goto_on_success=make.section_id("next"),
                goto_on_failure=make.section_id("done"),
                goto_on_code={"2": make.section_id("other")},
                save_stdout_to="stdout",
                save_stderr_to="stderr",
                timeout=5,
            ),
            description="run",
        )

        assert result.is_ok()
        meta = result.unwrap()
        assert isinstance(meta, RunScriptMeta)
        assert meta.script == "echo ok"
        assert meta.save_stdout_to == "stdout"
        assert meta.save_stderr_to == "stderr"
        assert meta.timeout == 5
        assert meta.allowed_transtions == {make.section_id("next"), make.section_id("done"), make.section_id("other")}

    def test_markdown_construct_meta__requires_script_block(self) -> None:
        result = RunScript().markdown_construct_meta(
            artifact_id=machine_make.ARTIFACT_ID,
            source=workspace_make.section_source(),
            section_config=RunScriptConfig(
                id=make.section_id("start"),
                kind=make.primitive_kind("donna.primitives.sections.run_script.RunScript"),
            ),
            description="run",
        )

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], RunScriptMissingScriptBlock)

    def test_validate_section__collects_transition_config_errors(self) -> None:
        artifact = machine_make.artifact(
            [
                machine_make.artifact_section(
                    id=make.section_id("start"),
                    kind=make.primitive_kind("donna.primitives.sections.run_script.RunScript"),
                    meta=RunScriptMeta(
                        allowed_transtions={make.section_id("next")},
                        goto_on_code={"not-an-int": make.section_id("next"), "0": make.section_id("done")},
                    ),
                )
            ]
        )

        result = RunScript().validate_section(artifact, make.section_id("start"))

        assert result.is_err()
        assert {type(error) for error in result.unwrap_err()} == {
            RunScriptMissingGotoOnSuccess,
            RunScriptMissingGotoOnFailure,
            RunScriptInvalidExitCode,
            RunScriptGotoOnCodeIncludesZero,
        }

    def test_execute_section__stores_outputs_and_adds_selected_next_work_unit(self, mocker: MockerFixture) -> None:
        runtime_context = make.FakeRuntimeContext()
        mocker.patch("donna.primitives.sections.run_script.context", return_value=runtime_context)
        mocker.patch.object(run_script.workspace_config, "project_dir", return_value=Path("/project"))
        run = mocker.patch.object(run_script, "_run_script", return_value=("stdout", "stderr", 2))
        artifact = machine_make.artifact(
            [
                machine_make.artifact_section(
                    id=make.section_id("start"),
                    kind=make.primitive_kind("donna.primitives.sections.run_script.RunScript"),
                    title="Run checks",
                    meta=RunScriptMeta(
                        allowed_transtions={
                            make.section_id("next"),
                            make.section_id("done"),
                            make.section_id("other"),
                        },
                        script="echo ok",
                        save_stdout_to="stdout_key",
                        save_stderr_to="stderr_key",
                        goto_on_success=make.section_id("next"),
                        goto_on_failure=make.section_id("done"),
                        goto_on_code={"2": make.section_id("other")},
                    ),
                )
            ]
        )

        result = RunScript().execute_section(
            machine_make.task(),
            machine_make.work_unit(operation_id=make.operation_id("start")),
            artifact,
            make.section_id("start"),
        )

        assert result.is_ok()
        run.assert_called_once_with(script="echo ok", timeout=60, project_dir=Path("/project"))
        assert [message for _, message in runtime_context.journal.messages] == [
            "Run script `Run checks`",
            "Script finished `Run checks`, exit code: 2, has stdout: True, has stderr: True`",
        ]
        changes = result.unwrap()
        assert isinstance(changes[0], ChangeSetTaskContext)
        assert changes[0].key == "stdout_key"
        assert changes[0].value == "stdout"
        assert isinstance(changes[1], ChangeSetTaskContext)
        assert changes[1].key == "stderr_key"
        assert changes[1].value == "stderr"
        assert isinstance(changes[2], ChangeAddWorkUnit)
        assert changes[2].operation_id == machine_make.ARTIFACT_ID + ":other"


class TestCoerceOutput:
    def test_returns_empty_string_for_missing_output(self) -> None:
        assert _coerce_output(None) == ""

    def test_decodes_bytes_as_utf8_with_replacement(self) -> None:
        assert _coerce_output(b"ok \xff") == "ok \ufffd"

    def test_returns_string_output_unchanged(self) -> None:
        assert _coerce_output("ok") == "ok"
