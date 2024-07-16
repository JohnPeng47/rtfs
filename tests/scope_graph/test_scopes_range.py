from scope_graph.build_scopes import build_scope_graph
from scope_graph.scope_resolution.reference import Reference


def test_scopes_range():
    test_src = bytearray(
        """
    def main(x, y):
       a: typing.List = [x];
       b = y;

    should return typing.List, x, y as external parameters
    """,
        encoding="utf-8",
    )

    scope_graph = build_scope_graph(test_src, language="python")
