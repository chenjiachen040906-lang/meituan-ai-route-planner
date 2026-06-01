"""
Mock 数据模块 —— 后端未就绪时，前端可调用此模块模拟路线生成和调整。

用法：
    from mock_data import get_mock_route, adjust_mock_route
"""
import json
import os
from datetime import datetime, timedelta


# 加载本地 mock POI 数据
_POIS_PATH = os.path.join(os.path.dirname(__file__), "mock_pois.json")
with open(_POIS_PATH, encoding="utf-8") as _f:
    _ALL_POIS = json.load(_f)["pois"]

# 按类别索引，便于快速筛选
_POI_BY_CATEGORY: dict[str, list[dict]] = {}
for _poi in _ALL_POIS:
    _POI_BY_CATEGORY.setdefault(_poi["category"], []).append(_poi)


def _pick_pois(categories: list[str], count: int = 3) -> list[dict]:
    """从指定类别中按评分降序挑选 POI。"""
    pool = []
    for cat in categories:
        pool.extend(_POI_BY_CATEGORY.get(cat, []))
    pool.sort(key=lambda p: p["rating"], reverse=True)
    return pool[:count]


def _build_route_response(
    pois: list[dict],
    route_name: str,
    summary: str,
    start_time_str: str = "14:00",
) -> dict:
    """将 POI 列表组装成符合后端 RouteResponse 格式的字典。"""
    current = datetime.strptime(start_time_str, "%H:%M")
    route_pois = []
    total_cost = 0

    for i, poi in enumerate(pois):
        duration = 60 if poi["category"] == "餐饮" else 90
        arrival = current.strftime("%H:%M")
        cost = poi["avg_cost"]

        route_pois.append({
            "id": poi["id"],
            "name": poi["name"],
            "category": poi["category"],
            "sub_category": poi.get("sub_category", ""),
            "rating": poi.get("rating", 0),
            "avg_cost": cost,
            "arrival_time": arrival,
            "duration_minutes": duration,
            "stay_reason": poi.get("ugc_highlights", [""])[0] if poi.get("ugc_highlights") else "",
            "location": poi.get("location"),
            "business_hours": poi.get("business_hours", ""),
        })

        total_cost += cost
        current += timedelta(minutes=duration + 15)  # 15 分钟步行/交通

    total_duration = sum(p["duration_minutes"] for p in route_pois) + 15 * max(0, len(route_pois) - 1)

    return {
        "success": True,
        "route_name": route_name,
        "pois": route_pois,
        "total_cost_per_person": total_cost,
        "total_duration_minutes": total_duration,
        "summary": summary,
        "ai_reasoning": f"根据您的需求，我从三里屯区域的 POI 中挑选了评分较高的 {len(route_pois)} 个地点，"
                        f"兼顾餐饮和娱乐/购物，步行距离合理，时间安排紧凑。",
    }


def get_mock_route(user_input: str, constraints: dict | None = None) -> dict:
    """根据用户输入和约束条件返回一条 mock 路线。

    Args:
        user_input: 用户自然语言输入（仅用于判断偏好，不做真正 NLP）。
        constraints: 约束条件字典，可选键：time_budget, budget_per_person, preferences, people_count。

    Returns:
        符合后端 RouteResponse 接口格式的字典。
    """
    constraints = constraints or {}
    text = user_input.lower()

    # 根据关键词简单判断场景
    if any(kw in text for kw in ["吃", "美食", "餐厅", "饭"]):
        categories = ["餐饮", "餐饮", "购物"]
        name = "三里屯美食探店线"
        desc = "以三里屯人气餐厅为主线，穿插逛街购物，边吃边逛。"
    elif any(kw in text for kw in ["喝", "酒", "酒吧", "夜"]):
        categories = ["餐饮", "娱乐", "餐饮"]
        name = "三里屯微醺夜生活线"
        desc = "先吃顿好的，再去酒吧街感受三里屯夜生活。"
    elif any(kw in text for kw in ["逛", "购物", "买"]):
        categories = ["购物", "餐饮", "购物"]
        name = "三里屯逛街购物线"
        desc = "太古里和 SOHO 一站式购物，中间穿插美食补给。"
    else:
        categories = ["餐饮", "购物", "餐饮"]
        name = "三里屯半日休闲打卡线"
        desc = "精选三里屯热门打卡点，吃喝逛玩一网打尽。"

    budget = constraints.get("budget_per_person", 200)
    # 如果预算较低，排除高端餐厅
    if budget < 100:
        candidates = [p for p in _ALL_POIS if p["avg_cost"] <= budget or p["avg_cost"] == 0]
        if len(candidates) >= 3:
            picked = candidates[:3]
        else:
            picked = _pick_pois(categories, 3)
    else:
        picked = _pick_pois(categories, 3)

    return _build_route_response(picked, name, desc, start_time_str="14:00")


def adjust_mock_route(original_route: dict, feedback: str) -> dict:
    """根据用户反馈调整 mock 路线（简单修改第二站信息）。

    Args:
        original_route: 原始路线（RouteResponse 格式）。
        feedback: 用户调整反馈文本。

    Returns:
        调整后的路线，changed_poi_ids 标注变更位置。
    """
    route = json.loads(json.dumps(original_route))  # deep copy

    if len(route["pois"]) < 2:
        return route

    # 替换第二站为同类别的另一个 POI
    old_poi = route["pois"][1]
    old_cat = old_poi["category"]
    alternatives = [p for p in _ALL_POIS if p["id"] != old_poi["id"] and p["category"] == old_cat]

    if alternatives:
        import random
        new_poi_data = random.choice(alternatives)
        route["pois"][1] = {
            "id": new_poi_data["id"],
            "name": new_poi_data["name"],
            "category": new_poi_data["category"],
            "sub_category": new_poi_data.get("sub_category", ""),
            "rating": new_poi_data.get("rating", 0),
            "avg_cost": new_poi_data["avg_cost"],
            "arrival_time": old_poi["arrival_time"],
            "duration_minutes": old_poi["duration_minutes"],
            "stay_reason": new_poi_data.get("ugc_highlights", [""])[0] if new_poi_data.get("ugc_highlights") else "",
            "location": new_poi_data.get("location"),
            "business_hours": new_poi_data.get("business_hours", ""),
        }

    # 重新计算费用
    route["total_cost_per_person"] = sum(p["avg_cost"] for p in route["pois"])

    route["summary"] = f"已根据您的反馈「{feedback}」调整了第 2 站。"
    route["changed_poi_ids"] = [route["pois"][1]["id"]]
    route["ai_reasoning"] = f"收到反馈「{feedback}」，将第 2 站替换为 {route['pois'][1]['name']}，更符合您的需求。"

    return route
