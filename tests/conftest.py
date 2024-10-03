import pytest


@pytest.fixture(params=[True, False], ids=["headless", "no_headless"])
def headless(request):
    return request.param


@pytest.fixture(params=[True, False], ids=["debug", "no_debug"])
def debug(request):
    return request.param


@pytest.fixture(
    params=[True, False], ids=["debug_browser", "no_debug_browser"]
)
def debug_browser(request):
    return request.param