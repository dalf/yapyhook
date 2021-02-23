from yapyhook import FilterHook, Hook, PostHook, PreHook


def test_no_parameter():
    @Hook("test_no_parameter")
    def f():
        return True

    @PreHook("test_no_parameter")
    def prehook():
        return (True, False)

    assert f() is False


def test_filter():
    @Hook("test_filter")
    def f(x):
        for x in range(1, x):
            yield x

    @FilterHook("test_filter")
    def filter2(result, *args):
        for x in result:
            yield x * 10

    assert list(f(5)) == [10, 20, 30, 40]


def test_prehook_stop():
    @Hook("test_filter")
    def f(x):
        for x in range(1, x):
            yield x

    @PreHook("test_filter")
    def prehook(result, *args):
        return (True, [-1, -2, -3, -4])

    assert list(f(5)) == [-1, -2, -3, -4]


def test_posthook():

    prehook_args = None

    @Hook("test_posthook")
    def f(x):
        return x * 5

    @PostHook("test_posthook")
    def prehook(*args):
        nonlocal prehook_args
        prehook_args = args

    assert f(3) == 15
    assert prehook_args == (15, 3)
