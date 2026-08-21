"""DeepSeek 页面稳定定位规则。"""

MESSAGE_INPUT = (
    'textarea[name="search"]'
    '[placeholder*="给 DeepSeek 发送消息"]'
)

DEEP_THINK_TOGGLE = (
    '.ds-toggle-button:has-text("深度思考")'
)

SMART_SEARCH_TOGGLE = (
    '.ds-toggle-button:has-text("智能搜索")'
)

SEND_BUTTON = (
    'div[role="button"]'
    '.ds-button--primary'
    '.ds-button--filled'
    '.ds-button--circle'
)

ASSISTANT_MESSAGE_MAIN = (
    ".ds-assistant-message-main-content"
)

CITATION_MARKER = ".ds-markdown-cite"

QUICK_MAIN_MODE = (
    '[data-model-type="default"]'
    '[role="radio"]'
)

EXPERT_MAIN_MODE = (
    '[data-model-type="expert"]'
    '[role="radio"]'
)

VISION_MAIN_MODE = (
    '[data-model-type="vision"]'
    '[role="radio"]'
)

# Quick 模式完整来源列表。
SOURCE_CARD = (
    "a:"
    "has(.search-view-card__title):"
    "has(.search-view-card__snippet)"
)

SOURCE_CARD_TITLE = (
    ".search-view-card__title"
)

SOURCE_CARD_SNIPPET = (
    ".search-view-card__snippet"
)

SOURCE_CARD_ORDER = (
    ".ds-markdown-cite"
)

SOURCE_CARD_SITE_ICON = (
    "img.site_logo_img"
)

SOURCE_CARD_SITE_NAME = (
    "a:"
    "has(.search-view-card__title):"
    "span"
    "div:first-child span"
)
