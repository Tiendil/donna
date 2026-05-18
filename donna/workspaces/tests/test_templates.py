import pytest
from pytest_mock import MockerFixture

from donna.core.errors import EnvironmentErrorsProxy, ErrorsList
from donna.core.result import Err, Ok, Result
from donna.machine.templates import Directive, RenderMode
from donna.machine.templates_context import DirectiveContext
from donna.workspaces import errors as workspace_errors
from donna.workspaces import templates
from donna.workspaces.artifacts import ArtifactRenderContext
from donna.workspaces.templates import DirectivePathBuilder, render
from donna.workspaces.tests import make


class _Directive(Directive):
    analyze_id: str = "sample"

    def render_view(self, context: DirectiveContext, *argv: object) -> Result[object, ErrorsList]:
        return Ok(f"{context['render_mode']}:{','.join(str(arg) for arg in argv)}")


class _FailingDirective(Directive):
    analyze_id: str = "failing"

    def render_view(self, context: DirectiveContext, *argv: object) -> Result[object, ErrorsList]:
        return Err([workspace_errors.MarkdownArtifactWithoutSections(artifact_id=make.ARTIFACT_ID)])


class _ExplodingDirective(Directive):
    analyze_id: str = "exploding"

    def render_view(self, context: DirectiveContext, *argv: object) -> Result[object, ErrorsList]:
        raise RuntimeError("boom")


sample_directive = _Directive()
failing_directive = _FailingDirective()
exploding_directive = _ExplodingDirective()
not_directive = object()


class TestIsImportableModule:
    def test_returns_whether_module_can_be_imported(self) -> None:
        assert templates._is_importable_module("donna.workspaces.tests.test_templates")
        assert not templates._is_importable_module("donna.workspaces.tests.missing")


class TestDirectivePathBuilder:
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

        errors = exception_info.value.arguments["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.DirectivePathIncomplete)
        assert error.path == "donna"

    def test_call__reports_unimportable_module(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "missing", "sample_directive"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.arguments["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.DirectiveModuleNotImportable)
        assert error.module_path == "donna.workspaces.tests.missing"

    def test_call__reports_unexpected_import_error(self, mocker: MockerFixture) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "sample_directive"))
        mocker.patch("importlib.import_module", side_effect=RuntimeError("boom"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.arguments["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.DirectiveUnexpectedError)
        assert error.directive_path == "donna.workspaces.tests.test_templates.sample_directive"

    def test_call__reports_missing_directive(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "missing"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.arguments["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.DirectiveNotAvailable)
        assert error.module_path == "donna.workspaces.tests.test_templates"
        assert error.directive_name == "missing"

    def test_call__reports_non_directive_object(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "not_directive"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.arguments["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.DirectiveNotDirective)

    def test_call__passes_directive_result_errors(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "failing_directive"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"render_mode": RenderMode.view, "artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.arguments["errors"]
        assert isinstance(errors, list)
        error = errors[0]
        assert isinstance(error, workspace_errors.MarkdownArtifactWithoutSections)
        assert error.artifact_id == make.ARTIFACT_ID

    def test_call__reports_unexpected_directive_error(self) -> None:
        builder = DirectivePathBuilder(("donna", "workspaces", "tests", "test_templates", "exploding_directive"))

        with pytest.raises(EnvironmentErrorsProxy) as exception_info:
            builder({"render_mode": RenderMode.view, "artifact_id": make.ARTIFACT_ID})

        errors = exception_info.value.arguments["errors"]
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


class TestRender:
    def test_render__applies_template_directives(self) -> None:
        context = ArtifactRenderContext(primary_mode=RenderMode.view)

        result = render(
            make.ARTIFACT_ID,
            "{{ donna.workspaces.tests.test_templates.sample_directive('value') }}",
            context,
        )

        assert result.is_ok()
        assert result.unwrap() == "view:value"

    def test_render__returns_directive_errors(self) -> None:
        context = ArtifactRenderContext(primary_mode=RenderMode.view)

        result = render(
            make.ARTIFACT_ID,
            "{{ donna.workspaces.tests.test_templates.failing_directive() }}",
            context,
        )

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.MarkdownArtifactWithoutSections)
