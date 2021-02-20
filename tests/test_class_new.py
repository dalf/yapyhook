from hooks import Hook, HookClass, PreHook


def test_class_singleton():
    pre_f_args = ()

    @HookClass
    class C:

        SINGLETON = None

        def __new__(class_, *args, **kwargs):
            if not isinstance(class_.SINGLETON, class_):
                class_.SINGLETON = super().__new__(class_, *args, **kwargs)
            return class_.SINGLETON

        @Hook("test_class_singleton")
        def f(self, x):
            return x * 5

    @PreHook("test_class_singleton")
    def pre_f(*args):
        nonlocal pre_f_args
        pre_f_args = args

    i = C()
    i.f(3)

    assert i == C()
    assert pre_f_args == (i, 3)
