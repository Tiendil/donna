import pathlib

from donna.domain.paths import ProjectConfigPath
from donna.workspaces import errors as workspace_errors
from donna.workspaces.tests import make


class TestWorkspaceConfigError:
    def test_content_intro__includes_config_path(self, tmp_path: pathlib.Path) -> None:
        error = workspace_errors.ConfigParseFailed(
            config_path=ProjectConfigPath(tmp_path / "donna.toml"), details="bad"
        )

        assert error.content_intro() == f"Error in Donna config file '{tmp_path / 'donna.toml'}'"


class TestInternalError:
    def test_error_message__uses_workspace_internal_error_base(self) -> None:
        assert workspace_errors.InternalError().error_message() == "An internal error occurred"


class TestWorkspaceError:
    def test_cell_kind__uses_workspace_boundary(self) -> None:
        assert workspace_errors.WorkspaceError.model_fields["cell_kind"].default == "workspace_error"


class _EnvironmentErrorCase:
    def error(self) -> workspace_errors.WorkspaceError:
        raise NotImplementedError

    def test_model_dump__includes_structured_context(self) -> None:
        error = self.error()

        assert error.model_dump(mode="json")


class _InternalErrorCase:
    def error(self) -> workspace_errors.InternalError:
        raise NotImplementedError

    def test_error_message__formats_without_failure(self) -> None:
        assert self.error().error_message()


class TestConfigParseFailed(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.ConfigParseFailed(
            config_path=ProjectConfigPath(pathlib.Path("donna.toml")), details="bad"
        )


class TestConfigValidationFailed(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.ConfigValidationFailed(
            config_path=ProjectConfigPath(pathlib.Path("donna.toml")), details="bad"
        )


class TestWorkspaceConfigNotDiscovered(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.WorkspaceConfigNotDiscovered(config_name="donna.toml")


class TestWorkspaceAlreadyInitialized(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.WorkspaceAlreadyInitialized(config_path=ProjectConfigPath(pathlib.Path("donna.toml")))


class TestWorkspaceConfigNotFound(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.WorkspaceConfigNotFound(config_path=ProjectConfigPath(pathlib.Path("donna.toml")))


class TestWorkspaceConfigDirNotFound(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.WorkspaceConfigDirNotFound(config_path=ProjectConfigPath(pathlib.Path("donna.toml")))


class TestJournalCommandConfigInvalid(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.JournalCommandConfigInvalid(argument="{missing}", details="bad")


class TestJournalCommandFailed(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.JournalCommandFailed(command=["tool"], returncode=1, details="bad")


class TestArtifactError:
    def test_content_intro__includes_artifact_id(self) -> None:
        error = workspace_errors.ArtifactNotFound(artifact_id=make.ARTIFACT_ID)

        assert error.content_intro() == "Error for artifact '@/workflows/test.donna.md'"


class TestArtifactNotFound(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.ArtifactNotFound(artifact_id=make.ARTIFACT_ID)


class TestArtifactMultipleFiles(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.ArtifactMultipleFiles(artifact_id=make.ARTIFACT_ID)


class TestUnsupportedArtifactExtension(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.UnsupportedArtifactExtension(artifact_id=make.ARTIFACT_ID, extension=".md")


class TestMarkdownError:
    def test_content_intro__describes_source_without_artifact_id(self) -> None:
        error = workspace_errors.MarkdownArtifactWithoutSections()

        assert error.content_intro() == "Error in markdown source"

    def test_content_intro__describes_artifact_when_artifact_id_is_set(self) -> None:
        error = workspace_errors.MarkdownArtifactWithoutSections(artifact_id=make.ARTIFACT_ID)

        assert error.content_intro() == "Error in markdown artifact '@/workflows/test.donna.md'"


class TestMarkdownUnsupportedCodeFormat(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.MarkdownUnsupportedCodeFormat(format="ini")


class TestMarkdownMultipleH1Sections(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.MarkdownMultipleH1Sections(artifact_id=make.ARTIFACT_ID)


class TestMarkdownH1SectionMustBeFirst(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.MarkdownH1SectionMustBeFirst(artifact_id=make.ARTIFACT_ID)


class TestMarkdownArtifactWithoutSections(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.MarkdownArtifactWithoutSections(artifact_id=make.ARTIFACT_ID)


class TestMarkdownMultipleConfigBlocksInSection(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.MarkdownMultipleConfigBlocksInSection(section_title="Section")


class TestMarkdownMultipleScriptBlocksInSection(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.MarkdownMultipleScriptBlocksInSection(section_title="Section")


class TestPrimitiveDoesNotSupportMarkdown(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.PrimitiveDoesNotSupportMarkdown(primitive_id="kind")


class TestTemplateDirectiveError:
    def test_content_intro__describes_directive_without_artifact_id(self) -> None:
        error = workspace_errors.DirectivePathIncomplete(path="directive")

        assert error.content_intro() == "Error in template directive"

    def test_content_intro__describes_directive_with_artifact_id(self) -> None:
        error = workspace_errors.DirectivePathIncomplete(path="directive", artifact_id=make.ARTIFACT_ID)

        assert error.content_intro() == "Error in template directive for artifact '@/workflows/test.donna.md'"


class TestDirectivePathIncomplete(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.DirectivePathIncomplete(path="directive")


class TestDirectiveModuleNotImportable(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.DirectiveModuleNotImportable(module_path="missing")


class TestDirectiveNotAvailable(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.DirectiveNotAvailable(module_path="module", directive_name="missing")


class TestDirectiveNotDirective(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.DirectiveNotDirective(module_path="module", directive_name="name")


class TestDirectiveUnexpectedError(_EnvironmentErrorCase):
    def error(self) -> workspace_errors.WorkspaceError:
        return workspace_errors.DirectiveUnexpectedError(directive_path="module.name", details="bad")


class TestMarkdownSectionsCountMismatch(_InternalErrorCase):
    def error(self) -> workspace_errors.InternalError:
        return workspace_errors.MarkdownSectionsCountMismatch(
            artifact_id=make.ARTIFACT_ID,
            original_count=1,
            analyzed_count=2,
        )


class TestGlobalConfigAlreadySet(_InternalErrorCase):
    def error(self) -> workspace_errors.InternalError:
        return workspace_errors.GlobalConfigAlreadySet()


class TestGlobalConfigNotSet(_InternalErrorCase):
    def error(self) -> workspace_errors.InternalError:
        return workspace_errors.GlobalConfigNotSet()
