import asyncio

import pytest
import pytest_asyncio

import choreographer as choreo

# PYTEST TIP:
# set capture=no to let all debug leak through
# if asyncio and pytest aren't playing nice, this will help,
# especially in fixtures- since they may buffer your outputs
# and can freeze w/o dumping the buffer

##### Parameterized Arguments
# Are used to re-run tests under different conditions


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


# --headless is the default flag for most tests, but you can set --no-headless if you want to watch
def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true", dest="headless", default=True)
    parser.addoption("--no-headless", dest="headless", action="store_false")


# browser fixture will supply a browser for you
@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def browser(request):
    headless = request.config.getoption("--headless")
    debug = request.config.get_verbosity() > 2
    debug_browser = None if debug else False
    browser = await choreo.Browser(
        headless=headless,
        debug=debug,
        debug_browser=debug_browser,
    )
    temp_dir = browser.tmp_dir
    yield browser
    try:
        await browser.close()
    except choreo.browser.BrowserClosedError:
        pass
    if temp_dir.exists:
        raise RuntimeError(f"Temporary directory not deleted successfully: {temp_dir}")


# add a timeout if tests requests browser
# but if tests creates their own browser they are responsible
# a fixture can be used to specify the timeout: timeout=10
# else it uses pytest.default_timeout
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_setup(item: pytest.Item):
    yield
    if "browser" in item.funcargs:
        raw_test_fn = item.obj
        timeouts = [k for k in item.funcargs if k.startswith("timeout")]
        timeout = (
            item.funcargs[timeouts[-1]] if len(timeouts) else pytest.default_timeout
        )
        if (
            item.get_closest_marker("asyncio") and timeout
        ):  # "closest" because markers can be function/session/package etc

            async def wrapped_test_fn(*args, **kwargs):
                try:
                    return await asyncio.wait_for(
                        raw_test_fn(*args, **kwargs),
                        timeout=timeout,
                    )
                except TimeoutError:
                    pytest.fail(
                        f"Test {item.name} failed a timeout. This can be extended, but shouldn't be. See conftest.py.",
                    )

            item.obj = wrapped_test_fn


def pytest_configure():
    # change this by command line TODO
    pytest.default_timeout = 5


# pytests capture-but-display mechanics for output are somewhat spaghetti
# more information here:
# https://github.com/pytest-dev/pytest/pull/12854
# is in the note above, capture=no will cancel all capture but also allow all error
# to bubble up without buffering, which is helpful since sometimes error break the
# buffering mechanics
@pytest.fixture(scope="function")
def capteesys(request):
    import warnings

    from _pytest import capture

    if hasattr(capture, "capteesys"):
        warnings.warn(
            (
                "You are using a polyfill for capteesys, but this"
                " version of pytest supports it natively- you may"
                f" remove the polyfill from your {__file__}"
            ),
            DeprecationWarning,
        )
        # Remove next two lines if you don't want to ever switch to native version
        yield request.getfixturevalue("capteesys")
        return
    capman = request.config.pluginmanager.getplugin("capturemanager")
    capture_fixture = capture.CaptureFixture(
        capture.SysCapture,
        request,
        _ispytest=True,
    )

    def _inject_start():
        self = capture_fixture  # closure seems easier than importing Type or Partial
        if self._capture is None:
            self._capture = capture.MultiCapture(
                in_=None,
                out=self.captureclass(1, tee=True),
                err=self.captureclass(2, tee=True),
            )
            self._capture.start_capturing()

    capture_fixture._start = _inject_start
    capman.set_fixture(capture_fixture)
    capture_fixture._start()
    yield capture_fixture
    capture_fixture.close()
    capman.unset_fixture()
