import pathlib
import shutil
import time

from donna.cli.types import FullArtifactIdArgument
from donna.world.config import config, config_dir


def dir() -> pathlib.Path:
    cfg = config()
    tmp_path = cfg.tmp_dir

    if not cfg.tmp_dir.is_absolute():
        tmp_path = config_dir() / tmp_path

    tmp_path.mkdir(parents=True, exist_ok=True)

    return tmp_path


def file_for_artifact(artifact_id: FullArtifactIdArgument, extention: str) -> pathlib.Path:
    directory = dir()

    directory.mkdir(parents=True, exist_ok=True)

    normalized_extension = extention.lstrip(".")
    artifact_file_name = f"{str(artifact_id).replace('/', '.')}.{int(time.time() * 1000)}.{normalized_extension}"

    return directory / artifact_file_name


def clear() -> None:
    shutil.rmtree(dir())
