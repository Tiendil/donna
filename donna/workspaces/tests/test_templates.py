from collections.abc import Iterator
from pathlib import Path

import pytest
from llm_tool_cli.config.tests.fixtures import project_settings
from llm_tool_cli.core import errors as llm_tool_errors
from llm_tool_cli.core.errors import EnvironmentError, EnvironmentErrorsProxy
from llm_tool_cli.core.result import Err, Ok, Result, UnwrapErrError, UnwrapError
from pytest_mock import MockerFixture

from donna.machine import ArtifactRenderContext
from donna.machine.templates import RENDER_CONTEXT_VIEW, Directive, RenderMode
from donna.machine.templates_context import DirectiveContext
from donna.workspaces import config as workspace_config
from donna.workspaces import errors as workspace_errors
from donna.workspaces import templates
from donna.workspaces.templates import DirectivePathBuilder, render
from donna.workspaces.tests import make
from donna.workspaces.tests.fixtures import default_workspace_config

__all__ = ["default_workspace_config", "project_settings"]
pytestmark = pytest.mark.usefixtures("project_settings")


class _Directive(Directive):
    analyze_id: str = "sample"

    def render_view(self, context: DirectiveContext, *argv: object) -> Result[object]:
        return Ok(f"{context['render_mode']}:{','.join(str(arg) for arg in argv)}")


class _FailingDirective(Directive):
    analyze_id: str = "failing"

    def render_view(self, context: DirectiveContext, *argv: object) -> Result[object]:
        return Err([workspace_errors.MarkdownArtifactWithoutSections(artifact_id=make.ARTIFACT_ID)])


class _ExplodingDirective(Directive):
    analyze_id: str = "exploding"

    def render_view(self, context: DirectiveContext, *argv: object) -> Result[object]:
        raise RuntimeError("boom")


class _SharedFailureDirective(Directive):
    analyze_id: str = "shared_failure"

    def render_view(self, context: DirectiveContext, *argv: object) -> Result[object]:
        return Err([EnvironmentError(code="shared.unavailable", message="Service unavailable")])


sample_directive = _Directive()
failing_directive = _FailingDirective()
exploding_directive = _ExplodingDirective()
shared_failure_directive = _SharedFailureDirective()
not_directive = object()


@pytest.fixture
def template_directory(tmp_path: Path) -> Iterator[Path]:
    directory = tmp_path / "templates"
    directory.mkdir()
    with workspace_config.config.scope(workspace_config.Config.model_validate({"template_dirs": ["./templates"]})):
        yield directory


class TestIsImportableModule:
    def test_returns_whether_module_can_be_imported(self) -> None:
        assert templates._is_importable_module("donna.workspaces.tests.test_templates")
        assert not templates._is_importable_module("donna.workspaces.tests.missing")


class TestDirectivePathBuilder:
    @pytest.mark.parametrize(
        "failure",
        [
            UnwrapError(error=[EnvironmentError(code="unexpected", message="Unexpected error")]),
            UnwrapErrError(value="successful result"),
            llm_tool_errors.ContextValueNotSet(details={"name": "donna_config"}),
        ],
    )
    def test_call__does_not_convert_internal_exceptions(
        self, mocker: MockerFixture, failure: llm_tool_errors.InternalError
    ) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "sample_directive"))
        mocker.patch.object(_Directive, "render_view", side_effect=failure)

        with pytest.raises(llm_tool_errors.InternalError) as raised:
            builder({"render_mode": RenderMode.view, "artifact_id": make.ARTIFACT_ID})

        assert raised.value == failure

    @pytest.mark.parametrize(
        "failure",
        [
            UnwrapError(error=[EnvironmentError(code="unexpected", message="Unexpected error")]),
            UnwrapErrError(value="successful result"),
            llm_tool_errors.ContextValueNotSet(details={"name": "donna_config"}),
        ],
    )
    def test_call__does_not_convert_internal_import_exceptions(
        self, mocker: MockerFixture, failure: llm_tool_errors.InternalError
    ) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "sample_directive"))
        mocker.patch("donna.workspaces.templates.importlib.import_module", side_effect=failure)

        with pytest.raises(llm_tool_errors.InternalError) as raised:
            builder({"render_mode": RenderMode.view, "artifact_id": make.ARTIFACT_ID})

        assert raised.value == failure

    def test_getattr__extends_directive_path(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces")).tests.test_templates.sample_directive

        result = builder({"render_mode": RenderMode.view, "artifact_id": make.ARTIFACT_ID}, "value")

        assert result == "view:value"

    def test_getitem__extends_directive_path(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces"))["tests"]["test_templates"]["sample_directive"]

        result = builder({"render_mode": RenderMode.view, "artifact_id": make.ARTIFACT_ID}, "value")

        assert result == "view:value"

    def test_call__applies_directive(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "sample_directive"))

        result = builder({"render_mode": RenderMode.view, "artifact_id": make.ARTIFACT_ID}, "value")

        assert result == "view:value"

    def test_call__reports_incomplete_path(self) -> None:
        builder = DirectivePathBuilder(("donna",))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.details["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.DirectivePathIncomplete)
        assert error.path == "donna"

    def test_call__reports_unimportable_module(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "missing", "sample_directive"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.details["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.DirectiveModuleNotImportable)
        assert error.module_path == "donna.workspaces.tests.missing"

    def test_call__reports_unexpected_import_error(self, mocker: MockerFixture) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "sample_directive"))
        mocker.patch("importlib.import_module", side_effect=RuntimeError("boom"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.details["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.DirectiveUnexpectedError)
        assert error.directive_path == "donna.workspaces.tests.test_templates.sample_directive"

    def test_call__reports_missing_directive(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "missing"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.details["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.DirectiveNotAvailable)
        assert error.module_path == "donna.workspaces.tests.test_templates"
        assert error.directive_name == "missing"

    def test_call__reports_non_directive_object(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "not_directive"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.details["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.DirectiveNotDirective)

    def test_call__passes_directive_result_errors(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "failing_directive"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"render_mode": RenderMode.view, "artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.details["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.MarkdownArtifactWithoutSections)
        assert error.artifact_id == make.ARTIFACT_ID

    def test_call__reports_unexpected_directive_error(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "exploding_directive"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"render_mode": RenderMode.view, "artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.details["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.DirectiveUnexpectedError)
        assert error.directive_path == "donna.workspaces.tests.test_templates.exploding_directive"


class TestDirectivePathUndefined:
    def test_getattr__returns_directive_builder_for_importable_module(self) -> None:
        value = templates.DirectivePathUndefined(name="donna").workspaces

        assert isinstance(value, DirectivePathBuilder)

    def test_getattr__returns_undefined_for_non_importable_module(self) -> None:
        value = templates.DirectivePathUndefined(name="missing").directive

        assert not isinstance(value, DirectivePathBuilder)


class TestEnv:
    def test_env__returns_cached_environment_with_directive_undefined(self) -> None:
        environment = templates.env()

        assert environment is templates.env()
        assert environment.undefined is templates.DirectivePathUndefined


class TestProjectTemplateLoader:
    def test_render__respects_template_order_and_exact_paths(self, tmp_path: Path) -> None:
        project = tmp_path / "project"
        shared = tmp_path / "shared"
        project.mkdir()
        shared.mkdir()
        (shared / "body.md").write_text('{% include "detail.txt" %}', encoding="utf-8")
        (shared / "detail.txt").write_text("{% block origin %}Shared{% endblock %} {{ topic }}", encoding="utf-8")
        (project / "detail.txt").write_text(
            '{% extends "@/shared/detail.txt" %}{% block origin %}Project{% endblock %}', encoding="utf-8"
        )
        source = '{% set topic = "café" %}{% include "body.md" %}\n' '{% include "@/shared/detail.txt" %}'
        config = workspace_config.Config.model_validate({"template_dirs": ["./project", "./shared"]})

        with workspace_config.config.scope(config):
            result = render(make.ARTIFACT_ID, source, RENDER_CONTEXT_VIEW)

        assert result.unwrap() == "Project café\nShared café"

    @pytest.mark.parametrize("name", ["missing.md", "@/templates/missing.md"])
    @pytest.mark.usefixtures("template_directory")
    def test_render__reports_the_original_name_of_a_missing_template(self, name: str) -> None:
        result = render(make.ARTIFACT_ID, f'{{% include "{name}" %}}', RENDER_CONTEXT_VIEW)

        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.TemplateNotFound)
        assert error.template == name

    @pytest.mark.parametrize("template_dirs", [[], ["./templates"]])
    def test_render__loads_exact_path_independently_of_template_dirs(
        self, tmp_path: Path, template_dirs: list[str]
    ) -> None:
        (tmp_path / "fragment.md").write_text("Project fragment", encoding="utf-8")
        (tmp_path / "templates").mkdir()
        (tmp_path / "templates" / "fragment.md").write_text("Search directory fragment", encoding="utf-8")
        config = workspace_config.Config.model_validate({"template_dirs": template_dirs})

        with workspace_config.config.scope(config):
            result = render(make.ARTIFACT_ID, '{% include "@/fragment.md" %}', RENDER_CONTEXT_VIEW)

        assert result.unwrap() == "Project fragment"

    def test_render__does_not_search_template_dirs_for_missing_exact_path(self, template_directory: Path) -> None:
        fallback = template_directory / "@"
        fallback.mkdir()
        (fallback / "fragment.md").write_text("Search directory fragment", encoding="utf-8")

        result = render(make.ARTIFACT_ID, '{% include "@/fragment.md" %}', RENDER_CONTEXT_VIEW)

        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.TemplateNotFound)
        assert error.template == "@/fragment.md"

    @pytest.mark.parametrize("name", ["../fragment.md", "@/templates/../fragment.md", "@/templates/./fragment.md"])
    def test_render__rejects_invalid_template_paths(self, template_directory: Path, name: str) -> None:
        (template_directory / "fragment.md").write_text("Content", encoding="utf-8")
        (template_directory.parent / "fragment.md").write_text("Outside the root", encoding="utf-8")

        result = render(make.ARTIFACT_ID, f'{{% include "{name}" %}}', RENDER_CONTEXT_VIEW)

        assert result.is_err(workspace_errors.TemplateNotFound)

    def test_render__loads_symlink_with_relative_name(self, template_directory: Path) -> None:
        original = template_directory / "original.md"
        original.write_text("Content", encoding="utf-8")
        (template_directory / "link.md").symlink_to(original)

        result = render(make.ARTIFACT_ID, '{% include "./link.md" %}', RENDER_CONTEXT_VIEW)

        assert result.unwrap() == "Content"


class TestRenderEnvironment:
    @pytest.mark.usefixtures("default_workspace_config")
    def test_allows_optional_includes_without_configured_roots(self) -> None:
        environment = templates.render_environment()
        template = environment.from_string('Before{% include "missing.md" ignore missing %} after')

        assert template.render() == "Before after"


class TestRender:
    def test_render__requires_workspace_config(self) -> None:
        with pytest.raises(llm_tool_errors.ContextValueNotSet):
            render(make.ARTIFACT_ID, "Content", RENDER_CONTEXT_VIEW)

    @pytest.mark.usefixtures("default_workspace_config")
    def test_render__returns_shared_errors_across_callback_bridge(self) -> None:
        result = render(
            make.ARTIFACT_ID,
            "{{ donna.workspaces.tests.test_templates.shared_failure_directive() }}",
            ArtifactRenderContext(primary_mode=RenderMode.view),
        )

        error = result.unwrap_err()[0]
        assert error.code == "shared.unavailable"
        assert error.format_message() == "Service unavailable"

    @pytest.mark.usefixtures("default_workspace_config")
    def test_render__applies_template_directives(self) -> None:
        context = ArtifactRenderContext(primary_mode=RenderMode.view)

        result = render(
            make.ARTIFACT_ID,
            "{{ donna.workspaces.tests.test_templates.sample_directive('value') }}",
            context,
        )

        assert result.is_ok()
        assert result.unwrap() == "view:value"

    @pytest.mark.usefixtures("default_workspace_config")
    def test_render__returns_directive_errors(self) -> None:
        context = ArtifactRenderContext(primary_mode=RenderMode.view)

        result = render(
            make.ARTIFACT_ID,
            "{{ donna.workspaces.tests.test_templates.failing_directive() }}",
            context,
        )

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.MarkdownArtifactWithoutSections)

    def test_render__included_template_uses_markdown_escaping_rules(self, template_directory: Path) -> None:
        (template_directory / "fragment.html").write_text("{{ text }}", encoding="utf-8")

        result = render(
            make.ARTIFACT_ID,
            '{% set text = "<plain>" %}{% include "fragment.html" %}',
            RENDER_CONTEXT_VIEW,
        )

        assert result.unwrap() == "<plain>"

    def test_render__reports_invalid_template_encoding(self, template_directory: Path) -> None:
        (template_directory / "fragment.md").write_bytes(b"\xff")

        result = render(make.ARTIFACT_ID, '{% include "fragment.md" ignore missing %}', RENDER_CONTEXT_VIEW)

        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.TemplateRenderFailed)
        assert "utf-8" in error.reason

    def test_render__reports_template_syntax_error_with_source_line(self, template_directory: Path) -> None:
        fragment = template_directory / "fragment.md"
        fragment.write_text("First line\n{% typo %}", encoding="utf-8")

        result = render(make.ARTIFACT_ID, '{% include "fragment.md" %}', RENDER_CONTEXT_VIEW)

        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.TemplateRenderFailed)
        assert f"{fragment}:2:" in error.reason
