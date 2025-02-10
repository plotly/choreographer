import asyncio
import logging

import logistro
import pytest
import pytest_asyncio

import choreographer as choreo
from choreographer import errors

_logger = logistro.getLogger(__name__)


@pytest.fixture(params=[True, False], ids=["enable_sandbox", ""])
def sandbox(request):
    return request.param


@pytest.fixture(params=[True, False], ids=["enable_gpu", ""])
def gpu(request):
    return request.param


@pytest.fixture(params=[True, False], ids=["headless", ""])
def headless(request):
    return request.param


# --headless is the default flag for most tests,
# but you can set --no-headless if you want to watch
def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true", dest="headless", default=True)
    parser.addoption("--no-headless", dest="headless", action="store_false")


# browser fixture will supply a browser for you
@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def browser(request):
    _logger.info("Fixture building browser.")
    headless = request.config.getoption("--headless")
    browser = await choreo.Browser(
        headless=headless,
    )
    yield browser
    _logger.info("Fixture closing browser.")
    try:
        await browser.close()
    except errors.BrowserClosedError:
        pass
    if browser._browser_impl.tmp_dir.exists:  # noqa: SLF001
        raise RuntimeError(
            "Temporary directory not deleted successfully: "
            f"{browser._browser_impl.tmp_dir.path}",  # noqa: SLF001
        )


# add a timeout if tests requests browser
# but if tests creates their own browser they are responsible
# a fixture can be used to specify the timeout: timeout=10
# else it uses pytest.default_timeout
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_setup(item):
    # not even sure if this working
    # typer doesn't like item: pytest.Item w/ funcargs
    # but this is the recommended way
    # some people say do trylast
    yield
    if "browser" in item.funcargs:
        _logger.info("Hook setting test timeout.")
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
                        f"Test {item.name} failed a timeout. "
                        "This can be extended, but shouldn't be. See conftest.py.",
                    )

            item.obj = wrapped_test_fn


def pytest_configure():
    # change this by command line TODO
    pytest.default_timeout = 20


# pytest shuts down its capture before logging/threads finish
@pytest.fixture(scope="session", autouse=True)
def cleanup_logging_handlers(request):
    capture = request.config.getoption("--capture") != "no"
    try:
        yield
    finally:
        if capture:
            _logger.info("Conftest cleaning up handlers.")
            for handler in logging.root.handlers[:]:
                handler.flush()
                if isinstance(handler, logging.StreamHandler):
                    logging.root.removeHandler(handler)
