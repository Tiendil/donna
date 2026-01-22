import types
import uuid
from typing import TYPE_CHECKING, Iterable

from donna.domain.ids import FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import (
    Artifact,
    ArtifactConfig,
    ArtifactConstructor,
    ArtifactContent,
    ArtifactKind,
    ArtifactMeta,
    ArtifactSection,
    ArtifactSectionConfig,
    ArtifactSectionKind,
    ArtifactSectionMeta,
    SectionConstructor,
    SectionContent,
)
from donna.machine.cells import Cell
from donna.machine.operations import FsmMode, OperationMeta
from donna.machine.workflows import WorkflowMeta

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class TextConfig(ArtifactSectionConfig):
    pass


class PythonModuleSectionConfig(ArtifactSectionConfig):
    pass


class ArtifactSectionTextKind(ArtifactSectionKind):
    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Text sections cannot be executed.")

    def construct_section(self, artifact_id: "FullArtifactId", section: SectionContent) -> ArtifactSection:
        data = dict(section.config)

        if "id" not in data:
            # TODO: we should replace this hack with a proper ID generator
            #       to keep that id stable between runs
            #       options:
            #       - a hash of the content
            #       - a sequential ID generator per artifact
            data["id"] = "text" + uuid.uuid4().hex.replace("-", "")

        config = TextConfig.parse_obj(data)

        return ArtifactSection(
            id=artifact_id.to_full_local(config.id),
            kind=config.kind,
            title=section.title,
            description=section.description,
            meta=ArtifactSectionMeta(),
        )


class PythonModuleSectionKind(ArtifactSectionKind):
    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Python module sections cannot be executed.")

    def construct_section(self, artifact_id: "FullArtifactId", section: SectionContent) -> ArtifactSection:
        data = dict(section.config)
        config_data = {
            "id": data.get("id"),
            "kind": data.get("kind"),
        }
        config = PythonModuleSectionConfig.parse_obj(config_data)

        return ArtifactSection(
            id=artifact_id.to_full_local(config.id),
            kind=config.kind,
            title=section.title,
            description=section.description,
            meta=ArtifactSectionMeta(),
        )


class PythonArtifact(ArtifactKind):
    def construct_artifact(self, source: ArtifactContent) -> Artifact:
        raise NotImplementedError("Python artifacts are constructed from modules, not markdown sources.")

    def construct_module_artifact(  # noqa: CCR001
        self,
        module: types.ModuleType,
        artifact_id: "FullArtifactId",
        kind_id: FullArtifactLocalId,
    ) -> Artifact | None:
        artifact_constructor: ArtifactConstructor | None = None

        for value in module.__dict__.values():
            if isinstance(value, ArtifactConstructor):
                if artifact_constructor is not None:
                    raise NotImplementedError("Artifact module must define only one ArtifactConstructor.")

                artifact_constructor = value

        if artifact_constructor is None:
            return None

        title = artifact_constructor.title
        description = artifact_constructor.description
        artifact_kind_id = artifact_constructor.config.kind

        if artifact_kind_id != kind_id:
            raise NotImplementedError(
                f"Artifact kind mismatch: constructor uses '{artifact_kind_id}', but expected '{kind_id}'."
            )

        sections: list[ArtifactSection] = []

        constructors: list[SectionConstructor] = []
        section_kind_overrides: dict[FullArtifactLocalId, ArtifactSectionKind] = {}

        for name, value in sorted(module.__dict__.items()):
            if not name.isidentifier():
                continue

            if name.startswith("_"):
                continue

            if isinstance(value, SectionConstructor):
                constructors.append(value)

                if value.entity is not None and isinstance(value.entity, ArtifactSectionKind):
                    section_id = artifact_id.to_full_local(value.config.id)
                    section_kind_overrides[section_id] = value.entity

        for constructor in constructors:
            section = constructor.build_section(
                artifact_kind=self,
                artifact_id=artifact_id,
                section_kind_overrides=section_kind_overrides,
            )
            sections.append(section)

        return Artifact(
            id=artifact_id,
            kind=artifact_kind_id,
            title=title,
            description=description,
            meta=ArtifactMeta(),
            sections=sections,
        )


class SpecificationKind(ArtifactKind):
    def construct_artifact(self, source: ArtifactContent) -> Artifact:
        title = source.head.title or str(source.id)
        description = source.head.description
        kind_id = ArtifactConfig.parse_obj(source.head.config).kind

        sections = [self.construct_section(source.id, section) for section in source.tail]

        return Artifact(
            id=source.id,
            kind=kind_id,
            title=title,
            description=description,
            meta=ArtifactMeta(),
            sections=sections,
        )


def find_not_reachable_operations(
    start_id: FullArtifactLocalId,  # noqa: CCR001
    transitions: dict[FullArtifactLocalId, set[FullArtifactLocalId]],
) -> set[FullArtifactLocalId]:
    reachable = set()
    to_visit = [start_id]

    while to_visit:
        current = to_visit.pop()

        if current in reachable:
            continue

        reachable.add(current)

        to_visit.extend(transitions.get(current, ()))

    all_operations = set()

    for from_id, target_ids in transitions.items():
        all_operations.add(from_id)
        all_operations.update(target_ids)

    return all_operations - reachable


class WorkflowKind(ArtifactKind):
    def construct_artifact(self, source: ArtifactContent) -> Artifact:
        title = source.head.title or str(source.id)
        description = source.head.description
        kind_id = ArtifactConfig.parse_obj(source.head.config).kind

        sections = [self.construct_section(source.id, section) for section in source.tail]

        start_operation_id = None

        for section in sections:
            assert isinstance(section.meta, OperationMeta)
            if section.meta.fsm_mode == FsmMode.start:
                start_operation_id = section.id
                break
        else:
            raise NotImplementedError(f"Workflow '{source.id}' does not have a start operation.")

        assert start_operation_id is not None

        return Artifact(
            id=source.id,
            kind=kind_id,
            title=title,
            description=description,
            meta=WorkflowMeta(start_operation_id=start_operation_id),
            sections=sections,
        )

    def validate_artifact(self, artifact: Artifact) -> tuple[bool, list[Cell]]:  # noqa: CCR001
        assert isinstance(artifact.meta, WorkflowMeta)

        start_operation_id: FullArtifactLocalId = artifact.meta.start_operation_id

        if artifact.get_section(start_operation_id) is None:
            return False, [
                Cell.build_meta(
                    kind="artifact_kind_validation",
                    id=str(artifact.id),
                    status="failure",
                    message=f"Start operation ID '{start_operation_id}' does not exist in the workflow.",
                )
            ]

        transitions = {}

        for section in artifact.sections:
            assert isinstance(section.meta, OperationMeta)

            if section.meta.fsm_mode == FsmMode.final and section.meta.allowed_transtions:
                return False, [
                    Cell.build_meta(
                        kind="artifact_kind_validation",
                        id=str(artifact.id),
                        status="failure",
                        message=f"Final operation '{section.id}' should not have outgoing transitions.",
                    )
                ]

            if section.meta.fsm_mode == FsmMode.start and section.id != start_operation_id:
                return False, [
                    Cell.build_meta(
                        kind="artifact_kind_validation",
                        id=str(artifact.id),
                        status="failure",
                        message=(
                            f"Operation '{section.id}' is marked as start but does not match the workflow's start"
                            f" operation ID '{start_operation_id}'."
                        ),
                    )
                ]

            if section.meta.fsm_mode == FsmMode.normal and not section.meta.allowed_transtions:
                return False, [
                    Cell.build_meta(
                        kind="artifact_kind_validation",
                        id=str(artifact.id),
                        status="failure",
                        message=(
                            f"Operation '{section.id}' must have at least one allowed transition or be marked as"
                            " final."
                        ),
                    )
                ]

            assert section.id is not None
            transitions[section.id] = set(section.meta.allowed_transtions)

        not_reachable_operations = find_not_reachable_operations(
            start_id=start_operation_id,
            transitions=transitions,
        )

        if not_reachable_operations:
            return False, [
                Cell.build_meta(
                    kind="artifact_kind_validation",
                    id=str(artifact.id),
                    status="failure",
                    message="The following operations are not reachable from the start operation: "
                    f"{', '.join(str(op_id) for op_id in not_reachable_operations)}.",
                )
            ]

        return True, [
            Cell.build_meta(
                kind="artifact_kind_validation",
                id=str(artifact.id),
                status="success",
            )
        ]


__all__ = [
    "ArtifactSectionTextKind",
    "PythonModuleSectionKind",
    "PythonArtifact",
    "SpecificationKind",
    "WorkflowKind",
    "TextConfig",
    "PythonModuleSectionConfig",
    "find_not_reachable_operations",
]
