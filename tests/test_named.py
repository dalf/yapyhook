from yapihook import Hook, HookClass, HookType, PreHook


def test_function_hooks_function():
    pre_f_args = ()

    @Hook("test")
    def f(x):
        return x * 5

    @PreHook("test")
    def pre_f(*args):
        nonlocal pre_f_args
        pre_f_args = args

    f(3)

    assert pre_f_args == (3,)
    assert Hook.HOOKS["test"][HookType.PRECALL][0] == pre_f

    # check weakref
    del pre_f
    assert len(Hook.HOOKS["test"][HookType.PRECALL]) == 0
    pre_f_args = ()
    f(4)
    assert pre_f_args == ()


def test_class_hooks_function():
    pre_args = ()

    @Hook("test2")
    def f(x):
        return x * 5

    @HookClass
    class AClass:
        @PreHook("test2")
        def pre(self, *args):
            nonlocal pre_args
            pre_args = (self, *args)

    a_instance = AClass()
    f(3)

    assert pre_args == (a_instance, 3)

    # check weakref
    del a_instance
    pre_args = ()
    f(3)
    assert pre_args == ()


def test_function_hooks_class():
    pre_f_args = ()

    @HookClass
    class C:
        @Hook("test_function_hooks_class")
        def f(self, x):
            return x * 5

    @PreHook("test_function_hooks_class")
    def pre_f(*args):
        nonlocal pre_f_args
        pre_f_args = args

    i = C()
    i.f(3)

    assert pre_f_args == (i, 3)

    # check weakref
    del pre_f
    pre_f_args = ()
    i.f(4)
    assert pre_f_args == ()
