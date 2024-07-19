from src.b import main2, C


def main():
    def func2():
        pass

    a = main2()
    pass


class A(C):
    @classmethod
    def func1():
        main2()
        pass
