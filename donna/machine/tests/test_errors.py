from donna.domain.ids import SectionId
from donna.machine.errors import ArtifactPrimarySectionMissing
from donna.machine.tests import make


class TestArtifactValidationError:
    def test_content_intro__describes_artifact_error(self) -> None:
        error = ArtifactPrimarySectionMissing(artifact_id=make.ARTIFACT_ID)

        assert error.content_intro() == "Error in artifact '@/workflows/test.donna.md'"

    def test_content_intro__describes_section_error(self) -> None:
        error = ArtifactPrimarySectionMissing(artifact_id=make.ARTIFACT_ID, section_id=SectionId("section"))

        assert error.content_intro() == "Error in artifact '@/workflows/test.donna.md', section 'section'"
