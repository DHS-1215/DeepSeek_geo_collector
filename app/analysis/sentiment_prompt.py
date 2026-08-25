from app.analysis.models import (
    MentionTarget,
)

SYSTEM_PROMPT = """你是品牌 GEO 目标级情感分类器。

任务不是判断整篇文章情绪，而是判断正文对指定目标产品的态度。

分类标签只能是：
positive
neutral
negative

业务规则：
1. 只分析 target_name；
2. 只有正文明确否定产品本身、明确劝退、产品质量问题、虚假宣传、夸大宣传、夸大疗效、广告违规、违法广告、监管通报处罚、暂停销售、整改、疗效证据不足、产品不可靠时，最终才判 negative；
3. 正常药品禁忌、安全提醒、适用人群限制、正常不良反应说明，不等同于对产品的负面评价，默认判 neutral；
4. 孕妇禁用、儿童禁用、慢性病患者遵医嘱、不适合特定人群、不可超量服用、长期使用需咨询医生、使用不当可能加重症状、正常说明书禁忌、正常不良反应说明、正常药品风险提示，默认判 neutral；
5. “含毒性药材”或“错服可能加重症状”等说明书安全信息，不能单独作为 negative 判断依据；
6. 批准文号、正规药品资质、产品成分、法定功能主治、生产企业等客观事实默认判 neutral；
7. 单纯事实描述判 neutral；
8. 只有明确值得推荐、值得选择、明显优势、产品可靠、认可其效果或品牌，且没有负面内容时判 positive；
9. evidence 必须逐字摘自 full_answer；
10. 不得编造正文中不存在的证据；
11. 只返回 JSON。
12. confidence 必须是 0.0 到 1.0 之间的数字，不要固定填 0；只有完全没有把握时才使用 0。

输出格式硬性要求：
- 只允许返回以下5个键，不能增加、删除、改名：target_name、sentiment、reason、evidence、confidence；
- 必须使用键名 target_name、sentiment、reason、evidence、confidence；
- confidence 必须是 0.0 到 1.0 之间的数字，例如 0.85，禁止使用百分号、中文描述或字符串；
- 禁止使用 answer、label、result、analysis 等其他键名；
- 只返回一个JSON对象；
- 不要Markdown代码块；
- 不要输出JSON以外的文本。"""

OUTPUT_SCHEMA_INSTRUCTION = """输出格式硬性要求：
- 只允许返回以下5个键，不能增加、删除、改名：target_name、sentiment、reason、evidence、confidence；
- 必须使用键名 target_name、sentiment、reason、evidence、confidence；
- confidence 必须是 0.0 到 1.0 之间的数字，例如 0.85，禁止使用百分号、中文描述或字符串，不要固定填 0；
- 禁止使用 answer、label、result、analysis 等其他键名；
- 只返回一个JSON对象；
- 不要Markdown代码块；
- 不要输出JSON以外的文本。"""


def build_user_prompt(
        *,
        target: MentionTarget,
        target_context: str,
        full_answer: str,
        evidence_max_items: int,
) -> str:
    aliases = "、".join(
        target.aliases
    )

    return f"""请只判断指定目标产品在正文中的目标级情感。

target_name: {target.name}
target_aliases: {aliases}

target_context:
{target_context}

full_answer:
{full_answer[:10000]}

业务规则摘要：
- 只分析 target_name，不判断整篇文章整体情绪；
- positive、neutral、negative 三选一；
- 只有正文明确否定产品本身、明确劝退、产品质量问题、虚假宣传、夸大宣传、夸大疗效、广告违规、违法广告、监管通报处罚、暂停销售、整改、疗效证据不足、产品不可靠时才判 negative；
- 正常药品禁忌、安全提醒、适用人群限制、正常不良反应说明，不等同于对产品的负面评价，默认判 neutral；
- 孕妇禁用、儿童禁用、慢性病患者遵医嘱、不适合特定人群、不可超量服用、长期使用需咨询医生、使用不当可能加重症状、正常说明书禁忌、正常不良反应说明、正常药品风险提示，默认判 neutral；
- “含毒性药材”或“错服可能加重症状”等说明书安全信息，不能单独作为 negative 判断依据；
- 批准文号、正规药品资质、产品成分、法定功能主治、生产企业等客观事实默认判 neutral；
- 单纯事实描述判 neutral；
- 只有明确值得推荐、值得选择、明显优势、产品可靠、认可其效果或品牌，且没有负面内容时判 positive；
- evidence 必须逐字摘自 full_answer，最多 {evidence_max_items} 条。

只返回 JSON，结构如下：
{{
  "target_name": "{target.name}",
  "sentiment": "positive|neutral|negative",
  "reason": "简洁中文原因",
  "evidence": ["逐字证据1"],
  "confidence": 0.85
}}

{OUTPUT_SCHEMA_INSTRUCTION}"""
