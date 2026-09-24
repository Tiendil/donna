from donna.core import errors


class _FormattedInternalError(errors.InternalError):
    message_template: str = "Broken {thing}"


class _SampleEnvironmentError(errors.EnvironmentError):
    cell_kind: str = "sample_error"
    code: str = "sample.error"
    message: str = "Sample failed."

    def content_intro(self) -> str:
        return "Sample"


class TestInternalError:
    def test_init__formats_keyword_arguments(self) -> None:
        error = _FormattedInternalError(thing="state")

        assert error.details == {"thing": "state"}
        assert error.message == "Broken state"
        assert str(error) == "Broken state"
        assert error.args == ("Broken state",)


class TestEnvironmentError:
    def test_content_intro__uses_subclass_behavior(self) -> None:
        error = _SampleEnvironmentError()

        assert error.content_intro() == "Sample"
