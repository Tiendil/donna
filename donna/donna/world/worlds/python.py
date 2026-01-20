import importlib
import importlib.resources
import importlib.util
import pathlib
import pkgutil
import types
from collections.abc import Callable
from typing import cast

from donna.domain.ids import ArtifactId, FullArtifactId, WorldId
from donna.machine.artifacts import Artifact, PythonArtifact
from donna.world.artifact_builder import construct_artifact_from_content
from donna.world.worlds.base import World as BaseWorld


class Python(BaseWorld):
    id: WorldId
    readonly: bool = True
    session: bool = False
    root: str

    def _artifact_module_name(self, artifact_id: ArtifactId) -> str:
        return f"{self.root}.{artifact_id}"

    _MARKDOWN_ROOTS = {"specifications", "workflows"}

    def _resource_root(self, root_name: str) -> importlib.resources.abc.Traversable | None:
        package = f"{self.root}.{root_name}"

        try:
            return importlib.resources.files(package)
        except ModuleNotFoundError:
            return None

    def _resource_path(self, artifact_id: ArtifactId) -> importlib.resources.abc.Traversable | None:
        parts = str(artifact_id).split(".")

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

    def _has_python(self, artifact_id: ArtifactId) -> bool:
        module_name = self._artifact_module_name(artifact_id)
        return importlib.util.find_spec(module_name) is not None

    def _has_markdown(self, artifact_id: ArtifactId) -> bool:
        resource_path = self._resource_path(artifact_id)
        return resource_path is not None and resource_path.is_file()

    def has(self, artifact_id: ArtifactId) -> bool:
        if self._has_markdown(artifact_id):
            return True

        return self._has_python(artifact_id)

    def _fetch_python(self, artifact_id: ArtifactId) -> Artifact:
        full_id = FullArtifactId((self.id, artifact_id))
        module_name = self._artifact_module_name(artifact_id)
        module = importlib.import_module(module_name)
        from donna.std import artifacts as std_artifacts

        kind = std_artifacts.python_artifact_kind

        if not isinstance(kind, PythonArtifact):
            raise NotImplementedError("Python artifact kind is not available")

        return kind.construct_module(module, full_id)

    def _fetch_markdown(self, artifact_id: ArtifactId) -> Artifact:
        full_id = FullArtifactId((self.id, artifact_id))
        resource_path = self._resource_path(artifact_id)

        if resource_path is None or not resource_path.is_file():
            raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

        content = resource_path.read_text(encoding="utf-8")
        return construct_artifact_from_content(full_id, content)

    def fetch(self, artifact_id: ArtifactId) -> Artifact:
        if self._has_markdown(artifact_id):
            return self._fetch_markdown(artifact_id)

        return self._fetch_python(artifact_id)

    def _fetch_source_markdown(self, artifact_id: ArtifactId) -> bytes:
        resource_path = self._resource_path(artifact_id)

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

    def fetch_source(self, artifact_id: ArtifactId) -> bytes:  # noqa: CCR001
        if self._has_markdown(artifact_id):
            return self._fetch_source_markdown(artifact_id)

        return self._fetch_source_python(artifact_id)

    def update(self, artifact_id: ArtifactId, content: bytes) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        if self._has_markdown(artifact_id):
            raise NotImplementedError(f"Artifact `{artifact_id}` is not a python module in world `{self.id}`")

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

        for module_info in pkgutil.walk_packages(spec.submodule_search_locations, prefix=f"{self.root}."):
            module_name = module_info.name
            artifact_name = module_name[len(self.root) + 1 :]

            if not ArtifactId.validate(artifact_name):
                continue

            python_artifacts.append(ArtifactId(artifact_name))

        return python_artifacts

    def _list_artifacts_markdown(self, artifact_prefix: ArtifactId) -> list[ArtifactId]:  # noqa: CCR001
        prefix_parts = str(artifact_prefix).split(".")

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
                artifact_name = ".".join(base_parts + parts + [stem])
                if ArtifactId.validate(artifact_name):
                    resource_artifacts.append(ArtifactId(artifact_name))

        if base_path.is_dir():
            walk(base_path, [])

        return resource_artifacts

    def list_artifacts(self, artifact_prefix: ArtifactId) -> list[ArtifactId]:  # noqa: CCR001
        if str(artifact_prefix).split(".", maxsplit=1)[0] in self._MARKDOWN_ROOTS:
            return self._list_artifacts_markdown(artifact_prefix)

        prefix_str = str(artifact_prefix)
        prefix_with_dot = f"{prefix_str}."
        return [
            artifact
            for artifact in self._list_artifacts_python()
            if str(artifact) == prefix_str or str(artifact).startswith(prefix_with_dot)
        ]

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
