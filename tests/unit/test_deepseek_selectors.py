from app.deepseek.selectors import (
    DEEP_THINK_TOGGLE,
    MESSAGE_INPUT,
    SEND_BUTTON,
)


def test_deepseek_selectors_do_not_use_hashed_classes() -> None:
    selectors = [
        MESSAGE_INPUT,
        DEEP_THINK_TOGGLE,
        SEND_BUTTON,
    ]

    for selector in selectors:
        assert "_52c986b" not in selector
        assert "_27c9245" not in selector
        assert "d96f2d2a" not in selector
