import pytest

from donna.core.result import Err, Ok, Result, UnwrapErrError, UnwrapError, unwrap_to_error


class TestResult:
    def test_ok__exposes_success_value(self) -> None:
        result: Result[int, str] = Ok(2)

        assert result.is_ok()
        assert not result.is_err()
        assert result.ok() == 2
        assert result.err() is None
        assert result.unwrap() == 2
        assert result.unwrap_or(3) == 2

    def test_ok__maps_success_value(self) -> None:
        result: Result[int, str] = Ok(2)

        mapped = result.map(lambda value: value + 1)
        mapped_error = result.map_err(lambda error: f"{error}!")

        assert mapped.unwrap() == 3
        assert mapped_error.unwrap() == 2

    def test_ok__unwrap_err_raises_internal_error(self) -> None:
        result: Result[int, str] = Ok(2)

        with pytest.raises(UnwrapErrError) as exc_info:
            result.unwrap_err()

        assert exc_info.value.arguments == {"value": 2}

    def test_err__exposes_error_value(self) -> None:
        result: Result[int, str] = Err("failure")

        assert not result.is_ok()
        assert result.is_err()
        assert result.ok() is None
        assert result.err() == "failure"
        assert result.unwrap_or(3) == 3

    def test_err__maps_error_value(self) -> None:
        result: Result[int, str] = Err("failure")

        mapped = result.map(lambda value: value + 1)
        mapped_error = result.map_err(lambda error: f"{error}!")

        assert mapped.err() == "failure"
        assert mapped_error.err() == "failure!"

    def test_err__unwrap_raises_internal_error_with_error_value(self) -> None:
        result: Result[int, str] = Err("failure")

        with pytest.raises(UnwrapError) as exc_info:
            result.unwrap()

        assert exc_info.value.arguments == {"error": "failure"}


class TestOk:
    def test_returns_success_result(self) -> None:
        assert Ok("value").unwrap() == "value"


class TestErr:
    def test_returns_error_result(self) -> None:
        assert Err("error").unwrap_err() == "error"


class TestUnwrapToError:
    def test_converts_unwrap_error_to_error_result(self) -> None:
        @unwrap_to_error
        def composed() -> Result[str, list[str]]:
            return Err(["failure"]).unwrap()

        result = composed()

        assert result.is_err()
        assert result.unwrap_err() == ["failure"]

    def test_preserves_success_result(self) -> None:
        @unwrap_to_error
        def composed() -> Result[str, list[str]]:
            return Ok("value")

        assert composed().unwrap() == "value"

    def test_does_not_hide_arbitrary_exceptions(self) -> None:
        @unwrap_to_error
        def composed() -> Result[str, list[str]]:
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            composed()
