import importlib
import importlib.resources
import importlib.util
import pathlib
import pkgutil
import types
from collections.abc import Callable
from typing import cast

from donna.domain.ids import ArtifactId, FullArtifactId, NamespaceId, WorldId
from donna.machine.artifacts import Artifact, PythonArtifact
from donna.world.artifact_builder import construct_artifact_from_content
from donna.world.primitives_register import register
from donna.world.worlds.base import World as BaseWorld


class Python(BaseWorld):
    id: WorldId
    readonly: bool = True
    session: bool = False
    root: str

    def _artifact_module_name(self, artifact_id: ArtifactId) -> str:
        return f"{self.root}.{artifact_id}"

    def _resource_root(self, namespace_id: NamespaceId) -> importlib.resources.abc.Traversable | None:
        package = f"{self.root}.{namespace_id}"

        try:
            return importlib.resources.files(package)
        except ModuleNotFoundError:
            return None

    def _resource_path(
        self, namespace_id: NamespaceId, artifact_id: ArtifactId
    ) -> importlib.resources.abc.Traversable | None:
        resource_root = self._resource_root(namespace_id)

        if resource_root is None:
            return None

        resource_name = f"{artifact_id.replace('.', '/')}.md"
        return resource_root.joinpath(resource_name)

    def _has_python(self, artifact_id: ArtifactId) -> bool:
        module_name = self._artifact_module_name(artifact_id)
        return importlib.util.find_spec(module_name) is not None

    def _has_markdown(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bool:
        resource_path = self._resource_path(namespace_id, artifact_id)
        return resource_path is not None and resource_path.is_file()

    def has(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bool:
        if namespace_id == NamespaceId("python"):
            return self._has_python(artifact_id)

        return self._has_markdown(namespace_id, artifact_id)

    def _fetch_python(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> Artifact:
        full_id = FullArtifactId((self.id, namespace_id, artifact_id))
        module_name = self._artifact_module_name(artifact_id)
        module = importlib.import_module(module_name)

        kind = register().get_artifact_kind_by_namespace(namespace_id)

        if kind is None or not isinstance(kind, PythonArtifact):
            raise NotImplementedError("Python artifact kind is not registered")

        return kind.construct_module(module, full_id)

    def _fetch_markdown(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> Artifact:
        full_id = FullArtifactId((self.id, namespace_id, artifact_id))
        resource_path = self._resource_path(namespace_id, artifact_id)

        if resource_path is None or not resource_path.is_file():
            raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

        content = resource_path.read_text(encoding="utf-8")
        return construct_artifact_from_content(full_id, content)

    def fetch(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> Artifact:
        if namespace_id == NamespaceId("python"):
            return self._fetch_python(namespace_id, artifact_id)

        return self._fetch_markdown(namespace_id, artifact_id)

    def _fetch_source_markdown(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bytes:
        resource_path = self._resource_path(namespace_id, artifact_id)

        if resource_path is None or not resource_path.is_file():
            raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

        return resource_path.read_bytes()

    def _fetch_source_python(self, artifact_id: ArtifactId) -> bytes:  # noqa: CCR001
        module_name = self._artifact_module_name(artifact_id)
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

    def fetch_source(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bytes:  # noqa: CCR001
        if namespace_id == NamespaceId("python"):
            return self._fetch_source_python(artifact_id)

        return self._fetch_source_markdown(namespace_id, artifact_id)

    def update(self, namespace_id: NamespaceId, artifact_id: ArtifactId, content: bytes) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        if namespace_id != NamespaceId("python"):
            raise NotImplementedError(f"Namespace `{namespace_id}` is not supported by world `{self.id}`")

        module_name = self._artifact_module_name(artifact_id)
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

    def _list_artifacts_python(self) -> list[ArtifactId]:
        spec = importlib.util.find_spec(self.root)

        if spec is None or spec.submodule_search_locations is None:
            return []

        python_artifacts: list[ArtifactId] = []

        for module_info in pkgutil.iter_modules(spec.submodule_search_locations):
            name = module_info.name

            if not name.isidentifier():
                continue

            python_artifacts.append(ArtifactId(name))

        return python_artifacts

    def _list_artifacts_markdown(self, namespace_id: NamespaceId) -> list[ArtifactId]:  # noqa: CCR001
        resource_root = self._resource_root(namespace_id)

        if resource_root is None:
            return []

        resource_artifacts: list[ArtifactId] = []

        for artifact_file in resource_root.iterdir():
            if not artifact_file.is_file():
                continue

            artifact_name = pathlib.PurePosixPath(artifact_file.name)

            if artifact_name.suffix != ".md":
                continue

            artifact_stem = artifact_name.stem

            if not artifact_stem.isidentifier():
                continue

            resource_artifacts.append(ArtifactId(artifact_stem))

        return resource_artifacts

    def list_artifacts(self, namespace_id: NamespaceId) -> list[ArtifactId]:  # noqa: CCR001
        if namespace_id == NamespaceId("python"):
            return self._list_artifacts_python()

        return self._list_artifacts_markdown(namespace_id)

    def get_modules(self) -> list[types.ModuleType]:
        # load only top-level .py files
        # it is the responsibility of the developer to import submodules within those files
        # if required

        modules = []

        module = importlib.import_module(f"{self.root}.code")

        if not hasattr(module, "__path__"):
            raise ValueError(f"{module.__name__} is not a package")

        for modinfo in pkgutil.iter_modules(module.__path__, module.__name__ + "."):
            module = importlib.import_module(modinfo.name)
            modules.append(module)

        return modules

    # TODO: How can the state be represented in the Python world?
    def read_state(self, name: str) -> bytes | None:
        raise NotImplementedError(f"World `{self.id}` does not support state storage")

    def write_state(self, name: str, content: bytes) -> None:
        raise NotImplementedError(f"World `{self.id}` does not support state storage")

    def initialize(self, reset: bool = False) -> None:
        pass

    def is_initialized(self) -> bool:
        return True
