import gc
from hooks import HookType, Hook, PreHook, PostHook, FilterHook, HookClass, CallHook


#########################################################################################

@HookClass
class AClassExample:

    @Hook('simple')
    def f(self, x):
        for x in range(1, x):
            yield x

    @PreHook('simple')
    def before(self, *args):
        print('AClassExample.before', self, args)

    @PostHook('simple')
    def after(self, *args):
        print('AClassExample.after', self, args)

    @FilterHook('simple')
    def filter(self, result, *args):
        print('AClassExample.filter', self, result, args)
        return result

    #@FilterHook('simple')
    def filter2(self, result, *args):
        print('AClassExample.filter', self, args)
        for x in result:
            yield x * 10

    @staticmethod
    def sm(*args):
        print('bob')

    @classmethod
    @Hook('test')
    def cm(cls):
        pass

    @staticmethod
    @PostHook('test')
    def cm_hook(self, *zz):
        print('cm_hook', zz)


a = AClassExample()
print('a=', a)

print('FUNCTIONS ', { k:v for k, v in CallHook.FUNCTIONS.items()})
print('METHODS   ', { k:v for k, v in CallHook.METHODS.items()})

for x in a.f(5):
    print(x)

AClassExample.cm()

print('## DEL ###############################################')

del a
del AClassExample

print({ k:v for k, v in CallHook.FUNCTIONS.items()})
print({ k:v for k, v in Hook.HOOKS.items()})

print('## GC ###############################################')

gc.collect()

print({ k:v for k, v in CallHook.FUNCTIONS.items()})
print({ k:v for k, v in Hook.HOOKS.items()})
