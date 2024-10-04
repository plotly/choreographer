import pytest
import pytest_asyncio
import devtools

@pytest.fixture(params=[True, False], ids=["headless", ""])
def headless(request):
    return request.param


@pytest.fixture(params=[True, False], ids=["debug", ""])
def debug(request):
    return request.param


@pytest.fixture(params=[True, False], ids=["debug_browser", ""])
def debug_browser(request):
    return request.param

@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def browser():
    browser = await devtools.Browser()
    yield browser
    await browser.close()
