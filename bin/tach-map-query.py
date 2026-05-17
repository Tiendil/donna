#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import PurePosixPath
import subprocess
import sys
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Print Tach file relations for one Donna artifact.")
    parser.add_argument("--direction", choices=("dependencies", "dependents"), required=True)
    parser.add_argument("--artifact", required=True)
    args = parser.parse_args()

    env = os.environ.copy()
    env["COMPOSE_IGNORE_ORPHANS"] = "true"

    completed = subprocess.run(
        [
            "./bin/dev.sh",
            "poetry",
            "run",
            "python",
            "-m",
            "tach",
            "map",
            "--direction",
            args.direction,
            "--output",
            "-",
        ],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        return completed.returncode

    try:
        dependency_map = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        print(f"could not parse tach map JSON: {error}", file=sys.stderr)
        return 1

    if not isinstance(dependency_map, dict):
        print("tach map JSON must be an object", file=sys.stderr)
        return 1

    artifact = _normalize_artifact(args.artifact)

    for dependency in sorted(_dependencies_for(dependency_map, artifact)):
        print(f"./{dependency}")

    return 0


def _normalize_artifact(artifact: str) -> str:
    normalized = artifact.strip()

    if normalized.startswith("@/"):
        normalized = normalized[2:]

    if normalized.startswith("./"):
        normalized = normalized[2:]

    return PurePosixPath(normalized).as_posix()


def _dependencies_for(dependency_map: dict[str, Any], artifact: str) -> list[str]:
    values = dependency_map.get(artifact, dependency_map.get(f"./{artifact}", []))

    if not isinstance(values, list):
        print(f"tach map value for {artifact!r} must be a list", file=sys.stderr)
        return []

    return [_normalize_artifact(value) for value in values if isinstance(value, str)]


if __name__ == "__main__":
    raise SystemExit(main())
