import typing

from yapyhook import HookClass, PreHook


def global_f(x):
    return x * 2


def test_globals():
    pre_global_f_args: typing.Tuple = ()

    @PreHook(globals(), "global_f")
    def pre_hook(*args):
        nonlocal pre_global_f_args
        pre_global_f_args = args

    assert global_f(5) == 10
    assert pre_global_f_args == (5,)


def test_function_hooks_function():
    def f(x):
        return x * 5

    # not possible


def test_class_hooks_function():
    def f(x):
        return x * 5

    # not possible


def test_function_hooks_class():
    pre_f_args: typing.Tuple = ()

    class C:
        def f(self, x):
            return x * 5

    @PreHook(C, "f")
    def pre_f(*args):
        nonlocal pre_f_args
        pre_f_args = args

    i = C()
    i.f(3)

    assert pre_f_args == (i, 3)


def test_function_hooks_instance():
    pre_f_args: typing.Tuple = ()

    class C:
        def f(self, x):
            return x * 5

    i = C()

    @PreHook(i, "f")
    def pre_f(*args):
        nonlocal pre_f_args
        pre_f_args = args

    i.f(3)

    # no self since i.f is a bound method
    assert pre_f_args == (3,)


def test_class_hooks_class():
    pre_args: typing.Tuple = ()

    class C:
        def f(self, x):
            return x * 5

    @HookClass
    class Intercept:
        @PreHook(C, "f", unbound_method=True)
        def pre(*args):
            nonlocal pre_args
            pre_args = args

    h = Intercept()
    i = C()
    i.f(3)

    assert pre_args == (h, i, 3)

    del h


def test_broken_class_hooks_class():
    pre_args: typing.Tuple = ()

    class C:
        def f(self, x):
            return x * 5

    # No @HookClass on purpose
    class Intercept:
        @PreHook(C, "f", unbound_method=True)
        def pre(*args):
            nonlocal pre_args
            pre_args = args

    h = Intercept()
    i = C()
    i.f(3)

    assert pre_args == ()

    del h


def test_reuse_anonymous_hook():

    prehook1_args: typing.Tuple = ()
    prehook2_args: typing.Tuple = ()

    class C:
        def f(self, x):
            return x * 5

    @PreHook(C, "f")
    def prehook1(*args, unbound_method=True):
        nonlocal prehook1_args
        prehook1_args = args

    @PreHook(C, "f")
    def prehook2(*args, unbound_method=True):
        nonlocal prehook2_args
        prehook2_args = args

    i = C()

    assert i.f(3) == 15
    assert prehook1_args == (i, 3)
    assert prehook2_args == (i, 3)
