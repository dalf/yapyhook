from hooks import Hook, PostHook


def test_repr():
    def f():
        return True

    h = Hook("test_repr")
    h(f)

    assert repr(h).startswith("<Hook 'test_repr' ")


def test_hook_delete():

    called = False

    @Hook("test_hook_delete")
    def f():
        return True

    @PostHook("test_hook_delete")
    def post_h(result):
        nonlocal called
        called = True

    assert called is False
    f()
    assert called is True

    del post_h
    called = False

    f()
    assert called is False


def test_hook_unregister():

    called = False

    @Hook("test_hook_unregister")
    def f():
        return True

    @PostHook("test_hook_unregister")
    def post_h(result):
        nonlocal called
        called = True

    assert called is False
    f()
    assert called is True

    assert Hook.unregister(func=post_h) is True
    called = False

    f()
    assert called is False
