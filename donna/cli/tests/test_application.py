import sys

import pytest
from pytest_mock import MockerFixture

from donna.cli.application import main
from donna.cli.tests import helpers


class TestInitialize:
    @pytest.mark.parametrize("option", ["-p", "--protocol"])
    @pytest.mark.parametrize("value", ["invalid", "{protocol}", "{"])
    def test_invalid_protocol_uses_shared_llm_diagnostic(self, option: str, value: str) -> None:
        result = helpers.invoke([option, value, "version"])

        assert result.exit_code == 1
        assert not result.stdout
        assert result.stderr.startswith("--DONNA-CELL ")
        assert result.stderr.count(" BEGIN--\n") == 1
        assert "kind=error\n" in result.stderr
        assert "code=invalid_arguments\n" in result.stderr
        assert value in result.stderr
        assert "human" in result.stderr
        assert "llm" in result.stderr
        assert "automation" in result.stderr


class TestMain:
    @pytest.fixture
    def initialized_settings(self, isolated_settings: None) -> None:
        """Keep the label unset so main must initialize it."""

    @pytest.mark.parametrize(
        ("arguments", "exit_code"),
        [(["skill"], 0), (["--protocol", "invalid", "version"], 1)],
    )
    def test_initializes_label_before_parsing(
        self,
        mocker: MockerFixture,
        capsys: pytest.CaptureFixture[str],
        arguments: list[str],
        exit_code: int,
    ) -> None:
        mocker.patch.object(sys, "argv", ["donna", *arguments])

        for _ in range(2):
            with pytest.raises(SystemExit) as caught:
                main()

            assert caught.value.code == exit_code
            captured = capsys.readouterr()
            output = captured.err if exit_code else captured.out
            assert not (captured.out if exit_code else captured.err)
            assert output.startswith("--DONNA-CELL ")
            assert ("code=invalid_arguments\n" if exit_code else "kind=skill\n") in output
