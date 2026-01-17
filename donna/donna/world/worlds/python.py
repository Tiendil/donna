import importlib
import importlib.util
import pathlib
import pkgutil
import types
from collections.abc import Callable
from typing import cast

from donna.domain.ids import ArtifactId, FullArtifactId, NamespaceId, WorldId
from donna.machine.artifacts import Artifact, PythonArtifact
from donna.world.primitives_register import register
from donna.world.worlds.base import World as BaseWorld


class Python(BaseWorld):
    id: WorldId
    readonly: bool = True
    session: bool = False

    def has(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bool:
        if namespace_id != NamespaceId("python"):
            return False

        return importlib.util.find_spec(str(artifact_id)) is not None

    def fetch(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> Artifact:
        if namespace_id != NamespaceId("python"):
            raise NotImplementedError(f"Namespace `{namespace_id}` is not supported by world `{self.id}`")

        module_name = str(artifact_id)
        module = importlib.import_module(module_name)
        full_id = FullArtifactId((self.id, namespace_id, artifact_id))

        kind = register().get_artifact_kind_by_namespace(namespace_id)

        if kind is None or not isinstance(kind, PythonArtifact):
            raise NotImplementedError("Python artifact kind is not registered")

        return kind.construct_module(module, full_id)

    def fetch_source(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bytes:  # noqa: CCR001
        if namespace_id != NamespaceId("python"):
            raise NotImplementedError(f"Namespace `{namespace_id}` is not supported by world `{self.id}`")

        module_name = str(artifact_id)
        spec = importlib.util.find_spec(module_name)

        if spec is None:
            raise NotImplementedError(f"Module `{module_name}` is not available")

        source: str | None = None

        if spec.loader is not None:
            get_source = getattr(spec.loader, "get_source", None)

            if get_source is not None:
                result = cast(Callable[[str], str | None], get_source)(module_name)

                if isinstance(result, str):
                    source = result

        if source is not None:
            return source.encode("utf-8")

        origin = spec.origin

        if origin in (None, "built-in"):
            raise NotImplementedError(f"Module `{module_name}` does not have source")

        assert origin is not None

        path = pathlib.Path(origin)

        if path.suffix == ".pyc":
            source_path = path.with_suffix(".py")
        else:
            source_path = path

        if not source_path.exists():
            raise NotImplementedError(f"Module `{module_name}` does not have source")

        return source_path.read_bytes()

    def update(self, namespace_id: NamespaceId, artifact_id: ArtifactId, content: bytes) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        if namespace_id != NamespaceId("python"):
            raise NotImplementedError(f"Namespace `{namespace_id}` is not supported by world `{self.id}`")

        module_name = str(artifact_id)
        spec = importlib.util.find_spec(module_name)

        if spec is None:
            raise NotImplementedError(f"Module `{module_name}` is not available")

        origin = spec.origin

        if origin in (None, "built-in"):
            raise NotImplementedError(f"Module `{module_name}` does not have source")

        assert origin is not None

        path = pathlib.Path(origin)

        if path.suffix == ".pyc":
            source_path = path.with_suffix(".py")
        else:
            source_path = path

        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(content)

    def list_artifacts(self, namespace_id: NamespaceId) -> list[ArtifactId]:
        if namespace_id != NamespaceId("python"):
            return []

        artifacts: list[ArtifactId] = []

        for module_info in pkgutil.iter_modules():
            name = module_info.name

            if not name.isidentifier():
                continue

            artifacts.append(ArtifactId(name))

        return artifacts

    def get_modules(self) -> list[types.ModuleType]:
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
