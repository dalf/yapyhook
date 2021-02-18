from hooks import HookType, Hook, PreHook, PostHook, FilterHook, HookClass


#########################################################################################

@Hook('simple')
def f(x):
    return x * 10


@PreHook('simple')
def before(*args):
    print('before', args)


@HookClass
class AClassExample:

    def __init__(self, name):
        self.name = name

    @PreHook('simple')
    def before(self, *args):
        print('AClassExample.before', self, args)


@HookClass
class ASubClassExample(AClassExample):
    pass


@HookClass
class AClassWithoutInit:

    @PreHook('simple')
    def before(self, *args):
        print('AClassWithoutInit.before', args)
        return (True, None)

    @PostHook('simple')
    def after(self, *args):
        print('AClassWithoutInit.after', args)


@HookClass
class AClassWithFilter:

    @FilterHook('simple')
    def filter(self, result, *args):
        return result * 20


a = AClassExample('a')
b = AClassExample('b')
c = ASubClassExample('c')
d = AClassWithoutInit()

del b

print('\n## call hook for before, a, c, d')
print('f=', repr(f(2)))

del d

print('\n## call hook for before, a, c')
print('f=', repr(f(2)))

e = AClassWithFilter()

print('\n## call hook for before, a, c, e')
print('f=', repr(f(2)))

del e

print('\n## call hook for before, a, c')
print('f=', repr(f(2)))

print('\n## Existing hooks')
print([ k for k in Hook.HOOKS['simple'].hook_types[HookType.PRECALL]])


###############################################################################
# Subclass
# make sure the asce.before is call only once

class AnotherSubClassExample(AClassExample):  # decorator not required. Make sure the deal with it

    def __init__(self, name):
        super().__init__(name)
        self.value = 5


asce = AnotherSubClassExample('AnotherSubClassExample')

print('\n## call hook for before, a, c, asce')
print('f=', repr(f(2)))



#########################################################################################


@Hook('limited_hook', allowed_hook_types={HookType.PRECALL, HookType.POSTCALL})
def g(x):
    return x / 5

try:
    @HookClass
    class AClassWithError:

        @FilterHook('limited_hook')
        def filter(self, result, *args):
            return result * 20
except ValueError as e:
    print('ValueError excepted exception', e)


###############################################################################
# Free hook

print('\n## call free hook: pre_h')

def h(x):
    return x + 2

hookname = Hook.new_undeclared_hook(globals(), 'h')
print('hookname=', hookname)


@PreHook(hookname)
def pre_h(x):
    print('pre_h', x)

print(repr(h(5)))


print('\n## call free hook: pre_i')

import module_for_example

Hook.new_undeclared_hook(module_for_example, 'i', 'hook_i')

@PreHook('hook_i')
def pre_i(x):
    print('before i')

print('i=', repr(module_for_example.i(5)))


###############################################################################
# Free hook on instance method

print('\n## Free hook on instance method')

class AddPrefix:

    def __new__(cls, *args, **kwargs): 
        instance = super().__new__(cls) 
        print('instance=', instance)
        return instance
    
    def __init__(self, prefix):
        self.prefix = prefix

    def f(self, value):
        return self.prefix + value


add_prefix_instance = AddPrefix('prefix')
addprefix_f_hookname = Hook.new_undeclared_hook(add_prefix_instance, 'f')

@PreHook(addprefix_f_hookname)
def addprefix_f_prehook(*args):
    print('Before AddPrefix.f', args)

print(add_prefix_instance.f('value'))


###############################################################################
# Free hook on class method

print('\n## Free hook on class method')

class AddPrefix2:

    def __new__(cls, *args, **kwargs): 
        instance = super().__new__(cls) 
        print('instance=', instance)
        return instance
    
    def __init__(self, prefix):
        self.prefix = prefix

    def f(self, value):
        return self.prefix + value


addprefix2_f_hookname = Hook.new_undeclared_hook(AddPrefix2, 'f')
@PreHook(addprefix2_f_hookname)
def addprefix2_f_prehook(*args):
    print('Before AddPrefix2.f', args)

print(AddPrefix2('prefix').f('value'))


###############################################################################

@HookClass
class Bidule:

    @Hook('bidule')
    def f(self, x):
        return x * 2

@PreHook('bidule')
def prehook_bidule(*args):
    print('prehook_bidule', args)

Bidule().f(5)

print("Hook['simple'][HookType.PRECALL]=", Hook['simple'][HookType.PRECALL])
