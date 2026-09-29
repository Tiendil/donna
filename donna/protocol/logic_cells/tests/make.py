from donna.machine.tests import make as machine_make
from donna.protocol import ArtifactSectionStatusCell


def section(**kwargs: object) -> ArtifactSectionStatusCell:
    values: dict[str, object] = {
        "artifact_id": machine_make.ARTIFACT_ID,
        "section_id": machine_make.PRIMARY_SECTION_ID,
        "section_kind": machine_make.PRIMITIVE_PATH,
        "section_primary": False,
        "title": "Step",
        "description": "Description",
    }
    values.update(kwargs)
    return ArtifactSectionStatusCell.model_validate(values)
