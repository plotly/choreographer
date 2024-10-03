import pytest


@pytest.fixture(params=[True, False], ids=["async_headless", "async_no_headless"])
def headless(request):
    return request.param


@pytest.fixture(params=[True, False], ids=["async_debug", "async_no_debug"])
def debug(request):
    return request.param


@pytest.fixture(
    params=[True, False], ids=["async_debug_browser", "async_no_debug_browser"]
)
def debug_browser(request):
    return request.param