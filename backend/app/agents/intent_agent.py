import json
from openai import OpenAI
from app.core.config import get_settings
from app.models.schemas import Constraints

SYSTEM_PROMPT = """你是一个出行意图理解助手。从用户的自然语言输入中提取结构化信息。

请提取以下字段，以 JSON 格式输出：
- area: 目标区域/地点（字符串）
- time_budget: 时间预算（"半天"/"一天"/"两天"/具体描述）
- start_time: 预计出发时间（HH:MM 格式，如果用户没说就返回 null）
- budget_per_person: 人均预算（整数，单位元，如果用户没说就返回 null）
- preferences: 偏好标签列表，从以下选项中选择：美食, 拍照, 户外, 文化, 购物, 亲子, 夜生活, 休闲
- people_count: 人数（整数，如果用户没说就返回 null）
- special_requirements: 特殊要求（字符串，没有就返回空字符串）

只输出 JSON，不要输出其他内容。"""


async def understand_intent(user_input: str, constraints: Constraints) -> dict:
    """从用户输入中提取结构化意图信息，并与显式约束合并。"""
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

    response = client.chat.completions.create(
        model=settings.model_name,
        max_tokens=500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    intent = json.loads(raw)

    # 显式约束覆盖 LLM 推断
    if constraints.start_time:
        intent["start_time"] = constraints.start_time
    if constraints.budget_per_person:
        intent["budget_per_person"] = constraints.budget_per_person
    if constraints.preferences:
        intent["preferences"] = constraints.preferences
    if constraints.people_count:
        intent["people_count"] = constraints.people_count
    if constraints.time_budget:
        intent["time_budget"] = constraints.time_budget

    return intent
