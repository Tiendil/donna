import os
import subprocess  # noqa: S404
import tempfile
from typing import TYPE_CHECKING, ClassVar, Iterator, cast

import pydantic

from donna.core import errors as core_errors
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import ArtifactSectionId, FullArtifactId
from donna.machine.artifacts import Artifact, ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta
from donna.machine.errors import ArtifactValidationError
from donna.machine.operations import OperationConfig, OperationKind, OperationMeta
from donna.world import markdown
from donna.world.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.primitives.operations.run_script."""


class RunScriptMissingGotoOnSuccess(ArtifactValidationError):
    code: str = "donna.workflows.run_script_missing_goto_on_success"
    message: str = "Run script operation `{error.section_id}` must define `goto_on_success`."
    ways_to_fix: list[str] = [
        'Add `goto_on_success = "<next_operation_id>"` to the operation config block.',
    ]


class RunScriptMissingGotoOnFailure(ArtifactValidationError):
    code: str = "donna.workflows.run_script_missing_goto_on_failure"
    message: str = "Run script operation `{error.section_id}` must define `goto_on_failure`."
    ways_to_fix: list[str] = [
        'Add `goto_on_failure = "<next_operation_id>"` to the operation config block.',
    ]


class RunScriptMissingScriptBlock(ArtifactValidationError):
    code: str = "donna.workflows.run_script_missing_script_block"
    message: str = "Run script operation `{error.section_id}` must include a single `donna script` code block."
    ways_to_fix: list[str] = [
        "Add exactly one fenced code block starting with ` ``` donna script ` in the operation body.",
    ]


class RunScriptMultipleScriptBlocks(ArtifactValidationError):
    code: str = "donna.workflows.run_script_multiple_script_blocks"
    message: str = "Run script operation `{error.section_id}` must include exactly one `donna script` code block."
    ways_to_fix: list[str] = [
        "Remove extra `donna script` code blocks so only one remains in the operation body.",
    ]


class RunScriptGotoOnCodeIncludesZero(ArtifactValidationError):
    code: str = "donna.workflows.run_script_goto_on_code_includes_zero"
    message: str = "Run script operation `{error.section_id}` must not map exit code 0 in `goto_on_code`."
    ways_to_fix: list[str] = [
        "Remove the `0` entry from `goto_on_code` and use `goto_on_success` instead.",
    ]


class RunScriptInvalidExitCode(ArtifactValidationError):
    code: str = "donna.workflows.run_script_invalid_exit_code"
    message: str = "Run script operation `{error.section_id}` has invalid exit code `{error.exit_code}`."
    ways_to_fix: list[str] = [
        'Use integer exit code keys in `goto_on_code` (e.g., `"1" = "next_op"`).',
    ]
    exit_code: str


class RunScriptConfig(OperationConfig):
    save_stdout_to: str | None = None
    save_stderr_to: str | None = None
    goto_on_success: ArtifactSectionId | None = None
    goto_on_failure: ArtifactSectionId | None = None
    goto_on_code: dict[str, ArtifactSectionId] = pydantic.Field(default_factory=dict)
    timeout: int = 60


class RunScriptMeta(OperationMeta):
    script: str | None = None
    save_stdout_to: str | None = None
    save_stderr_to: str | None = None
    goto_on_success: ArtifactSectionId | None = None
    goto_on_failure: ArtifactSectionId | None = None
    goto_on_code: dict[str, ArtifactSectionId] = pydantic.Field(default_factory=dict)
    timeout: int = 60


class RunScript(MarkdownSectionMixin, OperationKind):
    config_class: ClassVar[type[RunScriptConfig]] = RunScriptConfig

    def markdown_construct_meta(
        self,
        artifact_id: "FullArtifactId",
        source: markdown.SectionSource,
        section_config: ArtifactSectionConfig,
        description: str,
        primary: bool = False,
    ) -> Result[ArtifactSectionMeta, ErrorsList]:
        run_config = cast(RunScriptConfig, section_config)
        scripts = source.scripts()
        if not scripts:
            return Err([RunScriptMissingScriptBlock(artifact_id=artifact_id, section_id=run_config.id)])
        if len(scripts) > 1:
            return Err([RunScriptMultipleScriptBlocks(artifact_id=artifact_id, section_id=run_config.id)])

        script = scripts[0]
        allowed_transitions: set[ArtifactSectionId] = set()

        if run_config.goto_on_success is not None:
            allowed_transitions.add(run_config.goto_on_success)

        if run_config.goto_on_failure is not None:
            allowed_transitions.add(run_config.goto_on_failure)

        if run_config.goto_on_code:
            allowed_transitions.update(run_config.goto_on_code.values())

        return Ok(
            RunScriptMeta(
                fsm_mode=run_config.fsm_mode,
                allowed_transtions=allowed_transitions,
                script=script,
                save_stdout_to=run_config.save_stdout_to,
                save_stderr_to=run_config.save_stderr_to,
                goto_on_success=run_config.goto_on_success,
                goto_on_failure=run_config.goto_on_failure,
                goto_on_code=dict(run_config.goto_on_code),
                timeout=run_config.timeout,
            )
        )

    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterator["Change"]:
        from donna.machine.changes import ChangeAddWorkUnit, ChangeSetTaskContext

        meta = cast(RunScriptMeta, operation.meta)

        script = meta.script
        assert script is not None

        stdout, stderr, exit_code = _run_script(script, meta.timeout)

        if meta.save_stdout_to is not None:
            yield ChangeSetTaskContext(task_id=task.id, key=meta.save_stdout_to, value=stdout)

        if meta.save_stderr_to is not None:
            yield ChangeSetTaskContext(task_id=task.id, key=meta.save_stderr_to, value=stderr)

        next_operation = _select_next_operation(exit_code, meta)
        full_operation_id = unit.operation_id.full_artifact_id.to_full_local(next_operation)

        yield ChangeAddWorkUnit(task_id=task.id, operation_id=full_operation_id)

    def validate_section(  # noqa: CCR001
        self, artifact: Artifact, section_id: ArtifactSectionId
    ) -> Result[None, ErrorsList]:
        section = artifact.get_section(section_id).unwrap()

        meta = cast(RunScriptMeta, section.meta)

        errors: ErrorsList = []

        if meta.goto_on_success is None:
            errors.append(RunScriptMissingGotoOnSuccess(artifact_id=artifact.id, section_id=section_id))

        if meta.goto_on_failure is None:
            errors.append(RunScriptMissingGotoOnFailure(artifact_id=artifact.id, section_id=section_id))

        for code in meta.goto_on_code:
            try:
                parsed = int(code)
            except ValueError:
                errors.append(
                    RunScriptInvalidExitCode(
                        artifact_id=artifact.id,
                        section_id=section_id,
                        exit_code=code,
                    )
                )
                continue

            if parsed == 0:
                errors.append(RunScriptGotoOnCodeIncludesZero(artifact_id=artifact.id, section_id=section_id))

        if errors:
            return Err(errors)

        return Ok(None)


def _run_script(script: str, timeout: int) -> tuple[str, str, int]:  # noqa: CCR001
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile("w", prefix="donna-script-", delete=False) as temp:
            temp.write(script)
            temp.flush()
            temp_path = temp.name

        os.chmod(temp_path, 0o700)

        try:
            result = subprocess.run(  # noqa: S603
                [temp_path],
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                stdin=subprocess.DEVNULL,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = _coerce_output(exc.stdout)
            stderr = _coerce_output(exc.stderr)
            return stdout, stderr, 124

        return _coerce_output(result.stdout), _coerce_output(result.stderr), result.returncode
    finally:
        if temp_path is not None:
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass


def _select_next_operation(exit_code: int, meta: RunScriptMeta) -> ArtifactSectionId:
    if exit_code == 0:
        next_operation = meta.goto_on_success
    else:
        next_operation = meta.goto_on_code.get(str(exit_code))
        if next_operation is None:
            next_operation = meta.goto_on_failure

    assert next_operation is not None
    return next_operation


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    return value
