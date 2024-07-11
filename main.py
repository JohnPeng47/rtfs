from src.build_scopes import build_scope_graph

# test = """
# import namespace.abc

# class Hello:
#     def hello1(self):
#         self.a = 1
#         pass

#     def panzer(self):
#         pass
# """
test = """
def func1():
    a = 1
    b = 2

"""

# test = """
# class A:
#     def func1():
#         a = 1
#         b = 2


# def func1():
#     a = 1
# """


build_scope_graph(bytearray(test, encoding="utf-8"), language="python")
