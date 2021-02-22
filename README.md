## yapyhook

Yet Another Python Hook library

This code is experimental:
* Memory leak not checked but use weakref.
* Doesn't support edge cases (`@staticmethod`, `@classmethod`, some cases with asyncgenerator, etc...)
* *Should* be thread safe.

### Usage example

```python
from hooks import Hook, FilterHook, PreHook, PostHook


@Hook("example")
def f(x: int):
    for i in range(1, x):
        yield i


def example():
    result = [x for x in f(5)]
    assert result == [1, 2, 3, 4]

    @PreHook("example")
    def before(x):
        print(f'pre f({x})')

    @FilterHook("example")
    def double_filter(result, x):
        for i in result:
            yield i * 2

    @PostHook("example")
    def after(result, x):
        print(f'post f({x})={result}')

    result = [x for x in f(5)]
    print(result)
    assert result == [2, 4, 6, 8]

    del double_filter
    # or Hook.unregister(double_filter)

    result = [x for x in f(5)]
    print(result)
    assert result == [1, 2, 3, 4]

    @PreHook("example")
    def special_case(x):
        if x <= 1:
            return (True, [x].__iter__())

    result = [x for x in f(-10)]
    print(result)
    assert result == [-10]

if __name__ == '__main__':
    example()

    # Hooks are garbage collected
    result = [x for x in f(-10)]
    print(result)
    assert result == []
```
