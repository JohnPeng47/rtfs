from scope_graph.utils import TextRange


def range(start, end):
    return TextRange(
        start_byte=0, end_byte=0, start_point=(start, 0), end_point=(end, 0)
    )
