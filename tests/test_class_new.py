import typing

from yapyhook import Hook, HookClass, PreHook


def test_class_singleton():
    pre_f_args: typing.Tuple = ()

    @HookClass
    class C:

        SINGLETON = None

        def __new__(class_):
            if not isinstance(class_.SINGLETON, class_):
                class_.SINGLETON = super().__new__(class_)
            return class_.SINGLETON

        @Hook("test_class_singleton")
        def f(self, x: int) -> int:
            return x * 5

    @PreHook("test_class_singleton")
    def pre_f(*args) -> None:
        nonlocal pre_f_args
        pre_f_args = args

    i = C()
    i.f(3)

    assert i == C()
    assert pre_f_args == (i, 3)
