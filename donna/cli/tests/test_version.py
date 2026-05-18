from pytest_mock import MockerFixture

from donna.cli.tests import helpers


class TestVersion:
    def test_prints_package_version_line(self, mocker: MockerFixture) -> None:
        helpers.load_cli_commands()
        mocker.patch("donna.cli.commands.version.importlib.metadata.version", return_value="9.8.7")

        result = helpers.invoke(["version"])

        assert result.exit_code == 0
        assert result.output == "9.8.7\n"
