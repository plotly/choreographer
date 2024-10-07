import asyncio
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
    # this needs also to be set by command line TODO
    browser = await devtools.Browser()
    yield browser
    await browser.close()

@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def browser_verbose():
    browser = await devtools.Browser(debug=True, debug_browser=True)
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
    pytest.default_timeout = 3

# add this fixture to extend timeout
# there is 6 second max test length for all
# which kills all tests
@pytest.fixture(scope="session")
def timeout_long():
    return 6

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
    print("Shimming")
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
