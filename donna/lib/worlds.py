"""Shared world constructor instances for default configuration."""

from donna.world.worlds.filesystem import FilesystemWorldConstructor
from donna.world.worlds.python import PythonWorldConstructor

filesystem = FilesystemWorldConstructor()
python = PythonWorldConstructor()
