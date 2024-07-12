from pathlib import Path
from typing import Iterator, Tuple
from config import FILE_GLOB_ENDING, LANGUAGE

from src.codeblocks.namespace import NameSpace

SRC_EXT = FILE_GLOB_ENDING[LANGUAGE]


# TODO: replace with the lama implementation or something
class RepoFs:
    """
    Handles all the filesystem operations
    """

    def __init__(self, repo_path: Path):
        self.path = repo_path
        # TODO: fix this later to actually parse the Paths

    def get_files_content(self) -> Iterator[Tuple[Path, bytes]]:
        # TODO: multithread this
        for file in self.path.rglob(SRC_EXT):
            yield file, file.read_bytes()

    def match_file(self, ns_path: Path) -> Path:
        """
        Given a file abc/xyz, check if it exists in all_paths
        even if the abc is not aligned with the root of the path
        """

        for path in self._get_all_paths():
            # could be folder or path
            if path.match(f"**/{ns_path}") or path.match(f"**/{ns_path}{SRC_EXT}"):
                return path

        return None

    def _get_all_paths(self):
        all_paths = list(self.path.rglob(SRC_EXT))
        all_dirs = [p for p in self.path.rglob("*") if p.is_dir()]

        return all_paths + all_dirs
