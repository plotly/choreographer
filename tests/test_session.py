import warnings

import logistro
import pytest
import pytest_asyncio

import choreographer as choreo

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")

_logger = logistro.getLogger(__name__)


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def session(browser):
    _logger.info("testing...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", choreo.protocol.ExperimentalFeatureWarning)
        session_browser = await browser.create_session()
    yield session_browser
    await browser.close_session(session_browser)


@pytest.mark.asyncio
async def test_session_send_command(session):
    _logger.info("testing...")
    # Test valid request with correct command
    response = await session.send_command(command="Target.getTargets")
    assert "result" in response and "targetInfos" in response["result"]  # noqa: PT018 I like this assertion

    # Test invalid method name should return error
    response = await session.send_command(command="dkadklqwmd")
    assert "error" in response

    # Test int method should return error
    with pytest.raises(
        choreo.protocol.MessageTypeError,
    ):
        await session.send_command(command=12345)
