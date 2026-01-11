import pathlib


def first_donna_dir(donna_dir_name: str) -> pathlib.Path | None:
    """Get the first parent directory containing the donna directory.

    Search from the current working directory upwards for a folder with donna directory (.donna by default).
    """
    current_dir = pathlib.Path.cwd().resolve()

    for parent in [current_dir] + list(current_dir.parents):
        donna_path = parent / donna_dir_name
        if donna_path.is_dir():
            return parent

    return None


def donna_home_dir(donna_dir_name: str) -> pathlib.Path:
    """Get the donna home directory in the user's home folder."""
    return pathlib.Path.home() / donna_dir_name


def discover_project_dir(donna_dir_name: str) -> pathlib.Path:
    """Discover the project directory by looking for the donna directory in parent folders."""

    donna_dir = first_donna_dir(donna_dir_name)

    if donna_dir is None:
        raise NotImplementedError("Could not find project directory with donna directory")

    if donna_dir == donna_home_dir(donna_dir_name):
        raise NotImplementedError("The discovered donna directory is the home directory, not a project directory")

    return donna_dir
