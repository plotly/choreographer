class BrowserFailedError(RuntimeError):
    """An error for when the browser fails to launch."""


class BrowserClosedError(RuntimeError):
    """An error for when the browser is closed accidently (during access)."""
