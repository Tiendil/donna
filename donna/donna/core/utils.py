import pathlib


def project_dir(donna_dir_name: str) -> pathlib.Path:
    """Get the project directory

    Search from the current working directory upwards for a folder with donna directory (.donna by default).
    """
    current_dir = pathlib.Path.cwd().resolve()

    for parent in [current_dir] + list(current_dir.parents):
        donna_path = parent / donna_dir_name
        if donna_path.is_dir():
            return parent

    raise NotImplementedError(f"folder with '{donna_dir_name}' directory not found")
