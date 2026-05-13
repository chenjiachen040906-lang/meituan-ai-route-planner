import json
from anthropic import Anthropic
from app.core.config import get_settings
from app.models.schemas import POI, RouteResponse, Location

SYSTEM_PROMPT = """你是一个本地路线规划专家。根据用户意图和候选 POI 列表，规划一条最优路线。

规划要求：
1. 路线必须考虑地理距离，减少来回折返
2. 餐饮类 POI 安排在合理的用餐时间段（午餐 11:30-13:30，晚餐 17:30-19:30）
3. 每个 POI 的停留时间要合理（餐饮 60-90 分钟，景点 60-120 分钟，购物 60-90 分钟）
4. 检查营业时间是否冲突
5. 总预算不能超标
6. 给出每个 POI 的选择理由，结合 UGC 评价风格

输出严格 JSON 格式：
{
    "route_name": "路线名称",
    "pois": [
        {
            "id": "poi_id",
            "name": "名称",
            "arrival_time": "HH:MM",
            "duration_minutes": 60,
            "stay_reason": "选择理由"
        }
    ],
    "summary": "路线整体描述",
    "ai_reasoning": "推理过程"
}

只输出 JSON，不要输出其他内容。"""


def plan_route(intent: dict, candidate_pois: list[POI]) -> RouteResponse:
    """使用 LLM 规划最优路线。"""
    settings = get_settings()
    client = Anthropic(api_key=settings.anthropic_api_key)

    # 构建候选 POI 信息
    poi_info = []
    for poi in candidate_pois:
        info = {
            "id": poi.id,
            "name": poi.name,
            "category": poi.category,
            "sub_category": poi.sub_category,
            "rating": poi.rating,
            "avg_cost": poi.avg_cost,
            "business_hours": poi.business_hours,
        }
        if poi.location:
            info["address"] = poi.location.address
            info["lat"] = poi.location.lat
            info["lng"] = poi.location.lng
        poi_info.append(info)

    user_msg = f"""用户意图：{json.dumps(intent, ensure_ascii=False)}

候选 POI 列表：
{json.dumps(poi_info, ensure_ascii=False, indent=2)}

请规划最优路线。"""

    response = client.messages.create(
        model=settings.model_name,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    plan = json.loads(raw)

    # 构建完整 POI 列表
    poi_map = {poi.id: poi for poi in candidate_pois}
    full_pois = []
    total_cost = 0

    for item in plan.get("pois", []):
        base = poi_map.get(item["id"])
        if not base:
            continue
        full_pois.append(
            POI(
                id=base.id,
                name=base.name,
                category=base.category,
                sub_category=base.sub_category,
                rating=base.rating,
                avg_cost=base.avg_cost,
                arrival_time=item.get("arrival_time", ""),
                duration_minutes=item.get("duration_minutes", 60),
                stay_reason=item.get("stay_reason", ""),
                location=base.location,
                business_hours=base.business_hours,
            )
        )
        total_cost += base.avg_cost

    total_minutes = sum(p.duration_minutes for p in full_pois)
    people = intent.get("people_count", 1)

    return RouteResponse(
        success=True,
        route_name=plan.get("route_name", "推荐路线"),
        pois=full_pois,
        total_cost_per_person=total_cost,
        total_duration_minutes=total_minutes,
        summary=plan.get("summary", ""),
        ai_reasoning=plan.get("ai_reasoning", ""),
    )
