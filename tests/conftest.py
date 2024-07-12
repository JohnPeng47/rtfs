from scope_graph.utils import TextRange


def range(start, end):
    return TextRange(
        start_byte=start, end_byte=end, start_point=(0, 0), end_point=(0, 0)
    )
