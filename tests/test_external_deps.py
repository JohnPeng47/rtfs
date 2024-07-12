from scope_graph.build_scopes import build_scope_graph
from scope_graph.scope_resolution.reference import Reference


def get_exports_with_parameters():
    test_src = bytearray(
        """
    modeling the following code:
    import typing

    def main(x, y):
       a: typing.List = [x];
       b = y;

    should return typing.List, x, y as external parameters
    """,
        encoding="utf-8",
    )

    scope_graph = build_scope_graph(test_src, language="python")
    refs = set([ref.name(test_src) for ref in scope_graph.exports()])

    assert set(["x", "y", "typing.List"])


def get_external_refs_with_parameters():
    # modeling the following code:
    # import typing
    #
    # def main(x, y):
    #    a: typing.List = [x];
    #    b = y;
    #
    #
    # def main2(x2, y2):
    #   main(x2, y2)
    #
    # should return typing.List, x2, y2 as external parameters, while x, y are internal because
    # they are called in the root scope
    pass
