import pytest

from yapihook import Hook, HookClass, PreHook


def test_duplicate():
    @Hook("test")
    def f():
        return False

    with pytest.raises(ValueError):

        @Hook("test")
        def g():
            return True

    del f


def test_staticmethod():
    @Hook("test_classmethod")
    def f():
        return True

    with pytest.raises(ValueError):

        @HookClass
        class C:
            @PreHook("test_classmethod")
            @staticmethod
            def f(self):
                return True


def test_unknow():

    with pytest.raises(ValueError):

        @HookClass
        class C:
            @PreHook("test_unknow")
            @staticmethod
            def f(self):
                return True


def test_wrong_parameters():

    with pytest.raises(ValueError):

        @HookClass
        class C:
            @PreHook("test_unknow", "invalid")
            def f(self):
                return True
