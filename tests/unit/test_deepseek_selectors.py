from app.deepseek.selectors import (
    ASSISTANT_MESSAGE_MAIN,
    DEEP_THINK_TOGGLE,
    EXPERT_MAIN_MODE,
    MESSAGE_INPUT,
    QUICK_MAIN_MODE,
    SEND_BUTTON,
    SMART_SEARCH_TOGGLE,
    VISION_MAIN_MODE,
    SOURCE_CARD,
    SOURCE_CARD_ORDER,
    SOURCE_CARD_SITE_ICON,
    SOURCE_CARD_SNIPPET,
    SOURCE_CARD_TITLE,
)


def test_deepseek_selectors_do_not_use_hashed_classes() -> None:
    selectors = [
        MESSAGE_INPUT,
        DEEP_THINK_TOGGLE,
        SMART_SEARCH_TOGGLE,
        SEND_BUTTON,
        ASSISTANT_MESSAGE_MAIN,
        QUICK_MAIN_MODE,
        EXPERT_MAIN_MODE,
        VISION_MAIN_MODE,
        SOURCE_CARD,
        SOURCE_CARD_TITLE,
        SOURCE_CARD_SNIPPET,
        SOURCE_CARD_ORDER,
        SOURCE_CARD_SITE_ICON,
    ]

    hashed_classes = [
        "_52c986b",
        "_27c9245",
        "d96f2d2a",
        "_9f2341b",
        "_18572c1",
        "_31a22b0",
        "_321831d",
    ]

    for selector in selectors:
        for hashed_class in hashed_classes:
            assert hashed_class not in selector


def test_main_mode_selectors_use_semantic_attributes() -> None:
    assert 'data-model-type="default"' in QUICK_MAIN_MODE
    assert 'data-model-type="expert"' in EXPERT_MAIN_MODE
    assert 'data-model-type="vision"' in VISION_MAIN_MODE

    assert 'role="radio"' in QUICK_MAIN_MODE
    assert 'role="radio"' in EXPERT_MAIN_MODE
    assert 'role="radio"' in VISION_MAIN_MODE


def test_quick_source_selectors_use_semantic_classes() -> None:
    assert (
            ".search-view-card__title"
            in SOURCE_CARD
    )

    assert (
            ".search-view-card__snippet"
            in SOURCE_CARD
    )

    assert (
            SOURCE_CARD_TITLE
            == ".search-view-card__title"
    )

    assert (
            SOURCE_CARD_SNIPPET
            == ".search-view-card__snippet"
    )

    assert (
            SOURCE_CARD_ORDER
            == ".ds-markdown-cite"
    )

    assert (
            SOURCE_CARD_SITE_ICON
            == "img.site_logo_img"
    )
