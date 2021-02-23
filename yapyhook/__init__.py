# SPDX-License-Identifier: MIT

from __future__ import annotations

import enum
import inspect
import threading
import typing
import weakref
from functools import wraps

__all__ = ["HookType", "Hook", "PreHook", "PostHook", "FilterHook", "HookClass"]
T = typing.TypeVar("T")
F = typing.Callable[..., T]
WEAKREF_F = typing.Union[weakref.ReferenceType, weakref.WeakMethod]
T_ARGS = typing.List[typing.Any]
T_KWARGS = typing.Dict[str, typing.Any]


def is_first_parameter_self(f: F) -> bool:
    signature = inspect.signature(f)
    if not signature.parameters:
        return False
    return next(iter(signature.parameters), None) == "self"


def is_async_function(f: F) -> bool:
    return (
        not inspect.isasyncgenfunction(f)
        and inspect.iscoroutinefunction(f)
        or inspect.isawaitable(f)
    )


class HookType(enum.Enum):
    PRECALL = "precall"
    POSTCALL = "postcall"
    FILTERCALL = "filtercall"


class CallHook:

    UNBOUND_METHODS: typing.ClassVar[
        weakref.WeakKeyDictionary
    ] = weakref.WeakKeyDictionary()

    def __init__(
        self,
        hook_type: HookType,
        name_or_obj: typing.Union[str, typing.Any],
        key: typing.Optional[str] = None,
        unbound_method: bool = False,
    ):
        self.hook_type = hook_type
        self.unbound_method = unbound_method
        if not isinstance(name_or_obj, str) and isinstance(key, str):
            self.name = Hook.get_anonymous_hook_name(name_or_obj, key)
        elif isinstance(name_or_obj, str) and key is None:
            self.name = name_or_obj
        elif key is not None:
            raise ValueError("key has to be None if name_or_obj is a str")

        if self.name not in Hook.HOOKS:
            raise ValueError(f"{self.name!r} doesn't exit")

    def __call__(
        self,
        f: F,
        *args: T_ARGS,
        **kwargs: T_KWARGS,
    ) -> F:
        if isinstance(f, (classmethod, staticmethod)):
            raise ValueError("classmethod and staticmethod are not supported")

        f_is_method = inspect.ismethod(f)

        wref: WEAKREF_F = (
            weakref.WeakMethod(f) if f_is_method else weakref.ref(f)  # type: ignore
        )

        """
        There is no way to know if a function is a unbound method.

        Heuristic: check if the first parameter is "self".

        The unbound_method parameter overrides this value.

        We need to know if the function is unbound method:
        * to register the bound function in register_instance
          so "self" has the expected value on @PreHook, @PostHook, @FilterHook
        * not to call the unbound function when there is no @HookClass for class using hooks.
        """
        if self.unbound_method or (not f_is_method and is_first_parameter_self(f)):
            CallHook.UNBOUND_METHODS[f] = (self.name, self.hook_type)
        else:
            Hook.HOOKS[self.name].register(self.hook_type, wref)

        # See static method Hooks.delete
        f.__setattr__("__hook__", (self.name, self.hook_type))
        return f

    @staticmethod
    def register_instance(instance: typing.Any) -> None:
        for name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
            hook = CallHook.UNBOUND_METHODS.get(method.__func__)
            if hook:
                name, hook_type = hook
                Hook.HOOKS[name].register(hook_type, weakref.WeakMethod(method))


def create_or_hook_new_method(cls: typing.Type[T]) -> None:
    existing_new = cls.__new__
    if existing_new is None:

        def new_method(
            cls: typing.Type[T],
            *args: T_ARGS,
            **kwargs: T_KWARGS,
        ) -> T:
            instance = super().__new__(cls)  # type: ignore
            CallHook.register_instance(instance)
            return instance

    else:

        def new_method(
            cls: typing.Type[T],
            *args: T_ARGS,
            **kwargs: T_KWARGS,
        ) -> T:
            instance = existing_new(cls)
            CallHook.register_instance(instance)
            return instance

    setattr(cls, "__new__", new_method)


def HookClass(cls: typing.Type[T]) -> typing.Type[T]:
    if not getattr(cls, "__hooked__", False):
        create_or_hook_new_method(cls)
        setattr(cls, "__hooked__", True)
    return cls


class PreHook(CallHook):
    def __init__(
        self,
        name_or_obj: typing.Union[str, typing.Any],
        key: str = None,
        unbound_method: bool = False,
    ):
        super().__init__(HookType.PRECALL, name_or_obj, key, unbound_method)


class PostHook(CallHook):
    def __init__(
        self,
        name_or_obj: typing.Union[str, typing.Any],
        key: str = None,
        unbound_method: bool = False,
    ):
        super().__init__(HookType.POSTCALL, name_or_obj, key, unbound_method)


class FilterHook(CallHook):
    def __init__(
        self,
        name_or_obj: typing.Union[str, typing.Any],
        key: str = None,
        unbound_method: bool = False,
    ):
        super().__init__(HookType.FILTERCALL, name_or_obj, key, unbound_method)


class Hook:

    HOOKS = (
        weakref.WeakValueDictionary()
    )  # type: typing.ClassVar[weakref.WeakValueDictionary[str, Hook]]

    __slots__ = (
        "__weakref__",
        "name",
        "hook_types",
        "allowed_hook_types",
        "is_coroutine",
        "lock",
    )

    def __init__(
        self,
        name: str,
        allowed_hook_types: typing.Optional[typing.Set[HookType]] = None,
    ):
        if name in Hook.HOOKS:
            raise ValueError(f"Hook {name!r} already exists")

        self.name = name
        self.hook_types: typing.Dict[HookType, typing.List] = {}
        self.allowed_hook_types: typing.List[HookType] = (
            set(*allowed_hook_types) if allowed_hook_types else HookType  # type: ignore
        )
        self.is_coroutine = False
        self.lock = threading.RLock()
        for hook_type in HookType:
            self.hook_types[hook_type] = []
        Hook.HOOKS[self.name] = self

    def _iter_hooks(
        self, hook_type: HookType
    ) -> typing.Generator[typing.Callable, None, None]:
        hook_list = self.hook_types[hook_type]
        for weakref_hook in hook_list:
            o = weakref_hook()
            if o is not None:
                yield o
            else:
                with self.lock:
                    hook_list.remove(weakref_hook)

    def _create_wrapped_function(self, f: F) -> F:
        @wraps(f)
        def hooked(*args: T_ARGS, **kwargs: T_KWARGS) -> T:
            return_value = None

            # PRECALL
            for o in self._iter_hooks(HookType.PRECALL):
                r = o(*args, **kwargs)
                if r is not None and r[0] is True:
                    return_value = r[1]
                    break
            else:
                # CALL
                return_value = f(*args, **kwargs)

            # FILTERCALL
            for o in self._iter_hooks(HookType.FILTERCALL):
                return_value = o(return_value, *args, **kwargs)

            # POSTCALL
            for o in self._iter_hooks(HookType.POSTCALL):
                o(return_value, *args, **kwargs)

            return return_value

        return hooked

    def _create_wrapped_async(self, f: F) -> F:
        @wraps(f)
        async def hooked(*args: T_ARGS, **kwargs: T_KWARGS) -> T:
            return_value = None

            # PRECALL
            for o in self._iter_hooks(HookType.PRECALL):
                r = await o(*args, **kwargs)
                if r is not None and r[0] is True:
                    return_value = r[1]
                    break
            else:
                # CALL
                return_value = await f(*args, **kwargs)

            # FILTERCALL
            for o in self._iter_hooks(HookType.FILTERCALL):
                return_value = await o(return_value, *args, **kwargs)

            # POSTCALL
            for o in self._iter_hooks(HookType.POSTCALL):
                await o(return_value, *args, **kwargs)

            return return_value

        return hooked

    def __call__(self, f: F) -> F:
        """Run the hooks and the hooked method, respecting the location of hooks"""

        if not inspect.isfunction(f) and not inspect.ismethod(f):
            raise ValueError(f"{f} has to be a function or a method")
        self.is_coroutine = is_async_function(f)
        if self.is_coroutine:
            hooked = self._create_wrapped_async(f)
        else:
            hooked = self._create_wrapped_function(f)
        hooked.__setattr__("__hookname__", self.name)
        return hooked

    def register(
        self,
        hook_type: HookType,
        weakref_hook: WEAKREF_F,
    ) -> None:
        if not isinstance(weakref_hook, weakref.ref):
            raise ValueError(f"{weakref_hook!r} is not a weakref.ref")

        # check allowed_hook_types
        if hook_type not in self.allowed_hook_types:
            raise ValueError(f"{hook_type!r} not allowed")

        # check weakref_hook
        o = weakref_hook()
        if o is None:
            raise ValueError(f"{o} has been garbage collected")
        if not inspect.isfunction(o) and not inspect.ismethod(o):
            raise ValueError(f"{o} has to be a function or a method")

        # check async or not
        o_is_async = is_async_function(o)
        if o_is_async != self.is_coroutine:
            if self.is_coroutine:
                raise ValueError(f"{o} must be an async function")
            raise ValueError(f"{o} must not be an async function")

        # make sure there is no duplicate
        hook_list = self.hook_types[hook_type]
        with self.lock:
            if weakref_hook not in hook_list:
                hook_list.append(weakref_hook)

    @staticmethod
    def unregister(func: F = None) -> bool:
        hook_info = func.__hook__ if hasattr(func, "__hook__") else None  # type: ignore
        if isinstance(hook_info, tuple):
            hook = Hook.HOOKS.get(hook_info[0])
            if hook is not None:
                with hook.lock:
                    hook_list = hook.hook_types[hook_info[1]]
                    for i, callback_weakref in enumerate(hook_list):
                        if callback_weakref() == func:
                            del hook_list[i]
                            return True
        return False

    def __class_getitem__(cls, hook_name: str) -> Hook:
        """Allow to write: Hook['my_hook_name']"""
        return Hook.HOOKS[hook_name]

    def __getitem__(self, hook_type: HookType) -> typing.List[F]:
        """Allow to write: Hook['my_hook_name'][HookType.PRECALL]"""
        return list(self._iter_hooks(hook_type))

    def __repr__(self) -> str:
        return f"<Hook {self.name!r} {self.hook_types!r}>"

    @staticmethod
    def get_hook_name(f: F) -> typing.Optional[str]:
        return f.__hookname__ if hasattr(f, "__hookname__") else None  # type: ignore

    @staticmethod
    def get_anonymous_hook_name(obj: typing.Any, key: str) -> str:
        if isinstance(obj, dict):
            f = obj[key]
        else:
            f = getattr(obj, key)
        hook_name = Hook.get_hook_name(f)
        if hook_name is not None:
            # already hooked
            return hook_name
        hook_name = f"hook_{id(f)}"
        wrapped_f = Hook(hook_name)(f)
        if isinstance(obj, dict):
            obj[key] = wrapped_f
        else:
            setattr(obj, key, wrapped_f)
        return hook_name
