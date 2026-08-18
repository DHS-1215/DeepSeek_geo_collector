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
