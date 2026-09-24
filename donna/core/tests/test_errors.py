from donna.core import errors


class _SampleEnvironmentError(errors.EnvironmentError):
    cell_kind: str = "sample_error"
    code: str = "sample.error"
    message: str = "Sample failed."

    def content_intro(self) -> str:
        return "Sample"


class TestEnvironmentError:
    def test_content_intro__uses_subclass_behavior(self) -> None:
        error = _SampleEnvironmentError()

        assert error.content_intro() == "Sample"
