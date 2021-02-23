import typing

import pytest

from yapyhook import FilterHook, Hook, PostHook, PreHook


@pytest.mark.asyncio
async def test_no_parameter():
    @Hook("async_test_no_parameter")
    async def f() -> bool:
        return True

    @PreHook("async_test_no_parameter")
    async def prehook() -> typing.Tuple[bool, bool]:
        return (True, False)

    assert await f() is False


@pytest.mark.asyncio
async def test_filter():
    @Hook("async_test_filter")
    async def f(x: int) -> int:
        return 5

    @FilterHook("async_test_filter")
    async def filter(result: int, *args) -> int:
        return result * 2

    assert await f(5) == 10


@pytest.mark.asyncio
async def test_filter_generator():
    @Hook("async_test_filter_generator")
    async def f(x: int) -> typing.AsyncGenerator[int, None]:
        for i in range(1, x):
            yield i

    result = [x async for x in f(5)]
    assert result == [1, 2, 3, 4]

    @FilterHook("async_test_filter_generator")
    async def filter(result, *args):
        async for x in result:
            yield x * 2

    result = [x async for x in f(5)]
    assert result == [2, 4, 6, 8]


@pytest.mark.asyncio
async def test_posthook():
    posthook_args: typing.Tuple = ()

    @Hook("async_test_posthook")
    async def f(x: int) -> int:
        return x * 2

    @PostHook("async_test_posthook")
    async def posthook(*args):
        nonlocal posthook_args
        posthook_args = args

    assert await f(5) == 10
    assert posthook_args == (10, 5)
