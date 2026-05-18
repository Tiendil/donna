import ast
import pathlib


def _pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.strip("_").split("_"))


def _expected_test_class_name(symbol_name: str, *, symbol_is_class: bool) -> str:
    if symbol_is_class:
        return f"Test{symbol_name.lstrip('_')}"

    return f"Test{_pascal_case(symbol_name)}"


def _expected_test_class_for_node(node: ast.AST) -> str | None:
    if isinstance(node, ast.ClassDef):
        return _expected_test_class_name(node.name, symbol_is_class=True)

    if isinstance(node, ast.FunctionDef):
        return _expected_test_class_name(node.name, symbol_is_class=False)

    return None


def _production_module_symbols(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [class_name for node in tree.body if (class_name := _expected_test_class_for_node(node)) is not None]


def _production_module_paths() -> list[pathlib.Path]:
    workspace_dir = pathlib.Path(__file__).parents[1]
    return [path for path in sorted(workspace_dir.glob("*.py")) if path.name != "__init__.py"]


def _production_symbols() -> dict[str, list[str]]:
    symbols = {}

    for path in _production_module_paths():
        symbols[path.name] = _production_module_symbols(path)

    return symbols


def _test_class_names() -> set[str]:
    tests_dir = pathlib.Path(__file__).parent
    names = set()

    for path in tests_dir.glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                names.add(node.name)

    return names


class TestWorkspaceSymbolCoverage:
    def test_each_module_level_function_and_class_has_a_test_class(self) -> None:
        test_classes = _test_class_names()
        missing = {
            module_name: [class_name for class_name in expected_classes if class_name not in test_classes]
            for module_name, expected_classes in _production_symbols().items()
        }
        missing = {module_name: names for module_name, names in missing.items() if names}

        assert missing == {}
