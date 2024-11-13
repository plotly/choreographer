import asyncio

import pytest
import pytest_asyncio

import choreographer as choreo

# PYTEST TIP:
# set capture=no to let all debug leak through
# if asyncio and pytest aren't playing nice, this will help,
# especially in fixtures- since they may buffer your outputs
# and can freeze w/o dumping the buffer

@pytest.fixture(params=[True, False], ids=["enable_sandbox", ""])
def sandbox(request):
    return request.param

@pytest.fixture(params=[True, False], ids=["enable_gpu", ""])
def gpu(request):
    return request.param

@pytest.fixture(params=[True, False], ids=["headless", ""])
def headless(request):
    return request.param


@pytest.fixture(params=[True, False], ids=["debug", ""])
def debug(request):
    return request.param


@pytest.fixture(params=[True, False], ids=["debug_browser", ""])
def debug_browser(request):
    return request.param


def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true", dest="headless", default=True)
    parser.addoption("--no-headless", dest="headless", action="store_false")


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def browser(request):
    # this needs also to be set by command line TODO
    headless = request.config.getoption("--headless")
    debug = request.config.get_verbosity() > 2
    debug_browser = None if debug else False
    browser = await choreo.Browser(
        headless=headless, debug=debug, debug_browser=debug_browser
    )
    yield browser
    try:
        await browser.close()
    except choreo.browser.BrowserClosedError:
        pass



@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def browser_verbose():
    browser = await choreo.Browser(debug=True, debug_browser=None)
    yield browser
    await browser.close()

# add a 2 second timeout if there is a browser fixture
# we do timeouts manually in test_process because it
# does/tests its own browser.close()
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_setup(item: pytest.Item):
    yield

    if "browser" in item.funcargs or "browser_verbose" in item.funcargs:
        raw_test_fn = item.obj
        timeouts = [k for k in item.funcargs if k.startswith("timeout")]
        timeout = item.funcargs[timeouts[-1]] if len(timeouts) else pytest.default_timeout
        if item.get_closest_marker("asyncio") and timeout:
            async def wrapped_test_fn(*args, **kwargs):
                try:
                    return await asyncio.wait_for(
                            raw_test_fn(*args, **kwargs), timeout=timeout
                                )
                except TimeoutError:
                    pytest.fail(f"Test {item.name} failed a timeout. This can be extended, but shouldn't be. See conftest.py.")
            item.obj = wrapped_test_fn

def pytest_configure():
    # change this by command line TODO
    pytest.default_timeout = 5

# add this fixture to extend timeout
# there is 6 second max test length for all
# which kills all tests
@pytest.fixture(scope="session")
def timeout_long():
    return 8

@pytest.fixture(scope="function")
def capteesys(request):
    from _pytest import capture
    import warnings
    if hasattr(capture, "capteesys"):
        warnings.warn(( "You are using a polyfill for capteesys, but this"
                        " version of pytest supports it natively- you may"
                        f" remove the polyfill from your {__file__}"),
                        DeprecationWarning)
        # Remove next two lines if you don't want to ever switch to native version
        yield request.getfixturevalue("capteesys")
        return
    capman = request.config.pluginmanager.getplugin("capturemanager")
    capture_fixture = capture.CaptureFixture(capture.SysCapture, request, _ispytest=True)
    def _inject_start():
        self = capture_fixture # closure seems easier than importing Type or Partial
        if self._capture is None:
            self._capture = capture.MultiCapture(
                in_ = None,
                out = self.captureclass(1, tee=True),
                err = self.captureclass(2, tee=True)
            )
            self._capture.start_capturing()
    capture_fixture._start = _inject_start
    capman.set_fixture(capture_fixture)
    capture_fixture._start()
    yield capture_fixture
    capture_fixture.close()
    capman.unset_fixture()
