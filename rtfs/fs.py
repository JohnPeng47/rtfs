from pathlib import Path
from typing import Iterator, Tuple

from rtfs.utils import TextRange
from rtfs.config import FILE_GLOB_ENDING, LANGUAGE
from rtfs.repo_resolution.namespace import NameSpace

import logging

logger = logging.getLogger(__name__)

SRC_EXT = FILE_GLOB_ENDING[LANGUAGE]


# TODO: replace with the lama implementation or something
class RepoFs:
    """
    Handles all the filesystem operations
    """

    def __init__(self, repo_path: Path):
        self.path = repo_path
        self._all_paths = self._get_all_paths()

        # TODO: fix this later to actually parse the Paths

    def get_files_content(self) -> Iterator[Tuple[Path, bytes]]:
        for file in self._all_paths:
            if file.suffix == SRC_EXT:
                yield file, file.read_bytes()

    def get_file_range(self, path: Path, range: TextRange) -> bytes:
        if path.suffix == SRC_EXT:
            if range:
                return "\n".join(
                    path.read_text().split("\n")[
                        range.start_point.row : range.end_point.row
                    ]
                )

    # TODO: need to account for relative paths
    # we miss the following case:
    # - import a => will match any file in the repo that ends with "a"
    def match_file(self, ns_path: Path) -> Path:
        """
        Given a file abc/xyz, check if it exists in all_paths
        even if the abc is not aligned with the root of the path
        """

        for path in self._all_paths:
            path_name = path.name.replace(SRC_EXT, "")
            match_path = list(path.parts[-len(ns_path.parts) : -1]) + [path_name]

            if match_path == list(ns_path.parts):
                if path.suffix == SRC_EXT:
                    return path.resolve()
                elif path.is_dir():
                    return (path / "__init__.py").resolve()

        return None

    def _get_all_paths(self):
        """
        Return all source files matching language extension and directories
        """

        return [p for p in self.path.rglob("*") if p.suffix == SRC_EXT or p.is_dir()]
