## yapyhook

Yet Another Python Hook library

This code is experimental:
* Memory leak not checked but use weakref.
* Doesn't support edge cases (`@staticmethod`, `@classmethod`, some cases with asyncgenerator, etc...)
* *Should* be thread safe.

### Usage example

### Hook on function and generator

```python
from yapihook import Hook, FilterHook, PreHook, PostHook


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

### Hook on class 

```python
from yapihook import Hook, FilterHook, PreHook, PostHook

class SomeText:

    @Hook('SomeText.__init__')
    def __init__(self, text):
        self.text = text
        self.letters = [c for c in self.text]

    def reverse(self):
        return ''.join(self.letters[::-1])


def example_class():

    @PostHook('SomeText.__init__')
    def count_letters(result, self, text):
        self.count = len(self.letters)

    text = SomeText('yapihook')
    assert text.count == 8
    assert text.reverse() == 'koohipay'

    @FilterHook(text, 'reverse')  # anonymous hook
    def filter_reverse(result):  # hook on instance: no self
        return '!' + result + '!'

    assert text.reverse() == '!koohipay!'


if __name__ == '__main__':
    example_class()

    another_text = SomeText('some text')
    assert hasattr(another_text, 'letters') is True
    assert hasattr(another_text, 'count') is False
    assert another_text.reverse() == 'txet emos'
```
