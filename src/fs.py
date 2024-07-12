from pathlib import Path
from typing import Iterator
from config import FILE_GLOB_ENDING, LANGUAGE


# TODO: replace with the lama implementation or something
class RepoFs:
    """
    Handles all the filesystem operations
    """

    def __init__(self, repo_path: Path):
        self.path = repo_path

    def get_files_content(self) -> Iterator[bytes]:
        # TODO: multithread this
        for file in self.path.rglob(FILE_GLOB_ENDING[LANGUAGE]):
            yield file.read_bytes()

    def get_root_folder(self):
        pass
