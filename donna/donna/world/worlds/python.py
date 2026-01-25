import importlib
import importlib.resources
from typing import TYPE_CHECKING, cast

from donna.domain.ids import ArtifactId, FullArtifactId, WorldId
from donna.machine.artifacts import Artifact
from donna.world.sources import markdown as markdown_source
from donna.world.worlds.base import World as BaseWorld
from donna.world.worlds.base import WorldConstructor

if TYPE_CHECKING:
    from donna.world.config import WorldConfig


class Python(BaseWorld):
    id: WorldId
    readonly: bool = True
    session: bool = False
    package: str
    artifacts_root: str

    _MARKDOWN_ROOTS = {"usage", "work"}

    def _resource_root(self, root_name: str) -> importlib.resources.abc.Traversable | None:
        package = f"{self.artifacts_root}.{root_name}"

        try:
            return importlib.resources.files(package)
        except ModuleNotFoundError:
            return None

    def _resource_path(self, artifact_id: ArtifactId) -> importlib.resources.abc.Traversable | None:
        parts = str(artifact_id).split(":")

        if not parts or parts[0] not in self._MARKDOWN_ROOTS:
            return None

        if len(parts) == 1:
            return None

        resource_root = self._resource_root(parts[0])

        if resource_root is None:
            return None

        *dirs, file_name = parts[1:]
        resource_path = resource_root

        for part in dirs:
            resource_path = resource_path.joinpath(part)

        return resource_path.joinpath(f"{file_name}.md")

    def _has_markdown(self, artifact_id: ArtifactId) -> bool:
        resource_path = self._resource_path(artifact_id)
        return resource_path is not None and resource_path.is_file()

    def has(self, artifact_id: ArtifactId) -> bool:
        return self._has_markdown(artifact_id)

    def _fetch_markdown(self, artifact_id: ArtifactId) -> Artifact:
        full_id = FullArtifactId((self.id, artifact_id))
        resource_path = self._resource_path(artifact_id)

        if resource_path is None or not resource_path.is_file():
            raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

        content = resource_path.read_text(encoding="utf-8")
        from donna.world.config import config

        source_config = cast(markdown_source.Config, config().get_source_config("markdown"))
        return markdown_source.construct_artifact_from_markdown_source(
            full_id,
            content,
            source_config,
        )

    def fetch(self, artifact_id: ArtifactId) -> Artifact:
        return self._fetch_markdown(artifact_id)

    def _fetch_source_markdown(self, artifact_id: ArtifactId) -> bytes:
        resource_path = self._resource_path(artifact_id)

        if resource_path is None or not resource_path.is_file():
            raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

        return resource_path.read_bytes()

    def fetch_source(self, artifact_id: ArtifactId) -> bytes:  # noqa: CCR001
        return self._fetch_source_markdown(artifact_id)

    def update(self, artifact_id: ArtifactId, content: bytes) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        raise NotImplementedError(f"World `{self.id}` is read-only")

    def _list_artifacts_markdown(self, artifact_prefix: ArtifactId) -> list[ArtifactId]:  # noqa: CCR001
        prefix_parts = str(artifact_prefix).split(":")

        if not prefix_parts or prefix_parts[0] not in self._MARKDOWN_ROOTS:
            return []

        resource_root = self._resource_root(prefix_parts[0])

        if resource_root is None:
            return []

        resource_artifacts: list[ArtifactId] = []

        resource_path = self._resource_path(artifact_prefix)
        if resource_path is not None and resource_path.is_file():
            return [artifact_prefix]

        if len(prefix_parts) == 1:
            base_path = resource_root
            base_parts = [prefix_parts[0]]
        else:
            base_path = resource_root
            for part in prefix_parts[1:]:
                base_path = base_path.joinpath(part)
            base_parts = prefix_parts

        def walk(  # noqa: CCR001
            node: importlib.resources.abc.Traversable,
            parts: list[str],
        ) -> None:
            for entry in node.iterdir():
                if entry.is_dir():
                    walk(entry, parts + [entry.name])
                    continue

                if not entry.is_file() or not entry.name.endswith(".md"):
                    continue

                stem = entry.name[: -len(".md")]
                artifact_name = ":".join(base_parts + parts + [stem])
                if ArtifactId.validate(artifact_name):
                    resource_artifacts.append(ArtifactId(artifact_name))

        if base_path.is_dir():
            walk(base_path, [])

        return resource_artifacts

    def list_artifacts(self, artifact_prefix: ArtifactId) -> list[ArtifactId]:  # noqa: CCR001
        if str(artifact_prefix).split(":", maxsplit=1)[0] in self._MARKDOWN_ROOTS:
            return self._list_artifacts_markdown(artifact_prefix)

        return []

    # TODO: How can the state be represented in the Python world?
    def read_state(self, name: str) -> bytes | None:
        raise NotImplementedError(f"World `{self.id}` does not support state storage")

    def write_state(self, name: str, content: bytes) -> None:
        raise NotImplementedError(f"World `{self.id}` does not support state storage")

    def initialize(self, reset: bool = False) -> None:
        pass

    def is_initialized(self) -> bool:
        return True


class PythonWorldConstructor(WorldConstructor):
    def construct_world(self, config: "WorldConfig") -> Python:
        package = getattr(config, "package", None)

        if package is None:
            raise NotImplementedError(f"World config '{config.id}' does not define a python package")

        module = importlib.import_module(str(package))
        artifacts_root = getattr(module, "donna_artifacts_root", None)

        if artifacts_root is None:
            raise NotImplementedError(f"Package '{package}' does not define donna_artifacts_root")

        if not isinstance(artifacts_root, str):
            raise NotImplementedError(f"Package '{package}' defines invalid donna_artifacts_root")

        return Python(
            id=config.id,
            package=str(package),
            artifacts_root=artifacts_root,
            readonly=config.readonly,
            session=config.session,
        )
