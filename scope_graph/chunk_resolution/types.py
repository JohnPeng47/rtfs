from typing import List


class ChunkMetadata:
    file_path: str
    file_name: str
    span_ids: List[str]
    start_line: int
    end_line: int
