from llama_index.core import SimpleDirectoryReader


def ingest(repo_path: str):
    reader = SimpleDirectoryReader(
        input_dir=repo_path,
        filename_as_id=True,
        required_exts=[".py"],  # TODO: Shouldn't be hardcoded and filtered
        recursive=True,
    )
