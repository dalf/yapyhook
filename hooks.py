from __future__ import annotations
from functools import wraps

import threading
import weakref
import inspect
import typing
import enum


__all__ = ['HookType', 'Hook', 'PreHook', 'PostHook', 'FilterHook', 'HookClass']


class HookType(enum.Enum):
    PRECALL = "precall"
    POSTCALL = "postcall"
    FILTERCALL = "filtercall"


class CallHook:

    METHODS: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
    FUNCTIONS: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()

    def __init__(self, name, hook_type):
        self.name = name
        self.hook_type = hook_type
        if self.name not in Hook.HOOKS:
            raise ValueError(f'{self.name} doesn\'t exit')

    def __call__(self, f, *args, **kwargs):
        if inspect.ismethod(f):
            wref = weakref.WeakMethod(f)
        else:
            wref = weakref.ref(f)

        """
        There is no way to know if a function belongs to a class except some hacks.
        The most reliable one seems '.' in f.__qualname__

        We need to know if the function is method:
        * to register the bound function in register_instance 
          so "self" has the expected value on @PreHook, @PostHook, @FilterHook
        * not to call the unbound function there is no @HookClass for class using hooks.
        """
        if '.' in f.__qualname__:
            CallHook.METHODS[f] = (self.name, self.hook_type)
        else:
            CallHook.FUNCTIONS[f] = (self.name, self.hook_type)
            Hook.HOOKS[self.name].add(self.hook_type, wref)
        return f

    @staticmethod
    def register_instance(instance):
        for name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
            hook = CallHook.METHODS.get(method.__func__)
            if hook:
                name, hook_type = hook
                Hook.HOOKS[name].add(hook_type, weakref.WeakMethod(method))


def create_new(cls):
    existing_new = cls.__new__
    if existing_new is None:
        def new_init_method(cls, *args, **kwargs):
            instance = super().__new__(cls)
            CallHook.register_instance(instance)
            return instance
    else:
        def new_init_method(self, *args, **kwargs):
            instance = existing_new(self)
            CallHook.register_instance(instance)
            return instance
    setattr(cls, '__new__', new_init_method)


def HookClass(cls):
    if not getattr(cls, '__hooked__', False):
        create_new(cls)
        setattr(cls, '__hooked__', True)
    return cls


class Hook:

    HOOKS = weakref.WeakValueDictionary()

    __slots__ = '__weakref__', 'name', 'hook_types', 'allowed_hook_types', 'is_coroutine', 'lock'

    def __init__(self, name: str, allowed_hook_types: typing.Optional[typing.Set[HookType]] = None):
        if name in Hook.HOOKS:
            raise ValueError(f'Hook {name!r} already exists')

        self.name = name
        self.hook_types: typing.Dict[HookType, typing.List] = {}
        self.allowed_hook_types = [*allowed_hook_types] if allowed_hook_types else HookType
        self.is_coroutine = False
        self.lock = threading.RLock()
        for hook_type in HookType:
            self.hook_types[hook_type] = []
        Hook.HOOKS[self.name] = self

    def _iter_hooks(self, hook_type: HookType):
        hook_list = self.hook_types[hook_type]
        for weakref_hook in hook_list:
            o = weakref_hook()
            if o is not None:
                yield o
            else:
                with self.lock:
                    hook_list.remove(weakref_hook)

    def _create_wrapped_function(self, f):
        @wraps(f)
        def hooked(*args, **kwargs):
            return_value = None

            # PRECALL
            for o in self._iter_hooks(HookType.PRECALL):
                r = o(*args, **kwargs)
                if r is not None and r[0] == True:
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
                o(*args, **kwargs)

            return return_value

        return hooked

    def _create_wrapped_coroutine(self, f):
        @wraps(f)
        async def hooked(*args, **kwargs):
            return_value = None

            # PRECALL
            for o in self._iter_hooks(HookType.PRECALL):
                r = await o(*args, **kwargs)
                if r is not None and r[0] == True:
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
                await o(*args, **kwargs)

            return return_value

        return hooked

    def __call__(self, f):
        """Run the hooks and the hooked method, respecting the location of hooks"""

        if not inspect.isfunction(f) and not inspect.ismethod(f):
            raise ValueError(f'{f} has to be a function or a method')
        self.is_coroutine = inspect.iscoroutinefunction(f)
        if self.is_coroutine:
            hooked = self._create_wrapped_coroutine(f)
        else:
            hooked = self._create_wrapped_function(f)
        return hooked

    def add(self, hook_type, weakref_hook):
        if not isinstance(weakref_hook, weakref.ref):
            raise ValueError(f'{weakref_hook!r} is not a weakref.ref')

        # check allowed_hook_types
        if hook_type not in self.allowed_hook_types:
            raise ValueError(f'{hook_type!r} not allowed')

        # check weakref_hook
        o = weakref_hook()
        if not inspect.isfunction(o) and not inspect.ismethod(o):
            raise ValueError(f'{o} has to be a function or a method')

        # check async or not
        o_is_async = inspect.iscoroutinefunction(o)
        if o_is_async != self.is_coroutine:
            if self.is_coroutine:
                raise ValueError(f'{o} must be an async function')
            raise ValueError(f'{o} must not be an async function')
    
        # make sure there is no duplicate
        hook_list = self.hook_types[hook_type]
        with self.lock:
            if weakref_hook not in hook_list:
                hook_list.append(weakref_hook)

    def delete(self, hook_type, hook):
        hooks = self.hook_types[hook_type]
        with self.lock:
            for i, weakref_hook in enumerate(hooks):
                if weakref_hook() == hook:
                    del hooks[i]
                    break

    def __class_getitem__(cls, hook_name):
        """Allow to write: Hook['my_hook_name']"""
        return Hook.HOOKS[hook_name]

    def __getitem__(self, hook_type):
        """Allow to write: Hook['my_hook_name'][HookType.PRECALL]"""
        return list(self._iter_hooks(hook_type))

    @staticmethod
    def new_undeclared_hook(obj, key, hook_name = None):
        if isinstance(obj, dict):
            f = obj[key]
        else:
            f = getattr(obj, key)
        if hook_name is None:
            hook_name = 'hook_' + str(id(f))
        wrapped_f = Hook(hook_name)(f)
        if isinstance(obj, dict):
            obj[key] = wrapped_f
        else:
            setattr(obj, key, wrapped_f)
        return hook_name


class PreHook(CallHook):

    def __init__(self, name, *args):
        super().__init__(name, HookType.PRECALL)


class PostHook(CallHook):

    def __init__(self, name, *args):
        super().__init__(name, HookType.POSTCALL)


class FilterHook(CallHook):

    def __init__(self, name, *args):
        super().__init__(name, HookType.FILTERCALL)
