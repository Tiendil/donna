"""Shared world constructor instances for default configuration."""

from donna.workspaces.worlds.filesystem import FilesystemWorldConstructor
from donna.workspaces.worlds.python import PythonWorldConstructor

filesystem = FilesystemWorldConstructor()
python = PythonWorldConstructor()
