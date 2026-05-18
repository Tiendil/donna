import pathlib

from donna.workspaces import errors as workspace_errors
from donna.workspaces import utils


class TestFirstProjectDirWithConfig:
    def test_returns_nearest_parent_with_config(self, mocker: object, tmp_path: pathlib.Path) -> None:
        project = tmp_path / "project"
        nested = project / "nested"
        nested.mkdir(parents=True)
        (project / "donna.toml").write_text("version = 1", encoding="utf-8")
        mocker.patch("pathlib.Path.cwd", return_value=nested)

        assert utils.first_project_dir_with_config("donna.toml") == project

    def test_returns_none_when_config_is_not_found(self, mocker: object, tmp_path: pathlib.Path) -> None:
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        assert utils.first_project_dir_with_config("donna.toml") is None


class TestDiscoverProjectDir:
    def test_returns_discovered_project_dir(self, mocker: object, tmp_path: pathlib.Path) -> None:
        mocker.patch.object(utils, "first_project_dir_with_config", return_value=tmp_path)

        result = utils.discover_project_dir("donna.toml")

        assert result.is_ok()
        assert result.unwrap() == tmp_path

    def test_reports_missing_config(self, mocker: object) -> None:
        mocker.patch.object(utils, "first_project_dir_with_config", return_value=None)

        result = utils.discover_project_dir("donna.toml")

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.WorkspaceConfigNotDiscovered)
        assert error.config_name == "donna.toml"
