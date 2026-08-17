import pytest

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.core.exceptions import BrowserError


def test_page_before_start_raises_error() -> None:
    session = BrowserSession(
        load_settings()
    )

    with pytest.raises(
            BrowserError,
            match="has not been started",
    ):
        _ = session.page
