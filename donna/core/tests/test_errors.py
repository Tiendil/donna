from donna.core import errors


class _FormattedInternalError(errors.InternalError):
    message = "Broken {thing}"


class _SampleEnvironmentError(errors.EnvironmentError):
    cell_kind: str = "sample_error"
    code: str = "sample.error"
    message: str = "Sample failed."

    def content_intro(self) -> str:
        return "Sample"


class TestInternalError:
    def test_error_message__formats_keyword_arguments(self) -> None:
        error = _FormattedInternalError(thing="state")

        assert error.arguments == {"thing": "state"}
        assert error.error_message() == "Broken state"
        assert str(error) == "_FormattedInternalError: Broken state"


class TestEnvironmentError:
    def test_content_intro__uses_subclass_behavior(self) -> None:
        error = _SampleEnvironmentError()

        assert error.content_intro() == "Sample"

    def test_ways_to_fix__uses_independent_default_list(self) -> None:
        first = _SampleEnvironmentError()
        second = _SampleEnvironmentError()

        first.ways_to_fix.append("Fix it.")

        assert first.ways_to_fix == ["Fix it."]
        assert second.ways_to_fix == []


class TestEnvironmentErrorsProxy:
    def test_init__stores_errors_for_technical_unwrap_bridge(self) -> None:
        error = _SampleEnvironmentError()
        proxy = errors.EnvironmentErrorsProxy([error])

        assert proxy.arguments == {"errors": [error]}
