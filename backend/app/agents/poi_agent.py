import json
from pathlib import Path
from app.models.schemas import POI, Location

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_pois_cache: list[dict] | None = None


def _load_pois() -> list[dict]:
    global _pois_cache
    if _pois_cache is None:
        poi_file = DATA_DIR / "pois.json"
        if not poi_file.exists():
            return []
        _pois_cache = json.loads(poi_file.read_text(encoding="utf-8"))
    return _pois_cache


def retrieve_pois(intent: dict) -> list[POI]:
    """根据意图筛选候选 POI 列表。"""
    all_pois = _load_pois()
    if not all_pois:
        return []

    area = intent.get("area", "")
    preferences = intent.get("preferences", [])
    budget = intent.get("budget_per_person", 9999)
    time_budget = intent.get("time_budget", "半天")

    # 时间预算 → 最大 POI 数量
    max_pois = {"半天": 3, "一天": 5, "两天": 8}.get(time_budget, 4)

    candidates = []
    for poi in all_pois:
        # 区域过滤（模糊匹配）
        if area and area not in poi.get("location", {}).get("address", "") and area not in poi.get("name", ""):
            # 也检查 tags 里有没有区域信息
            if not any(area in tag for tag in poi.get("tags", [])):
                continue

        # 预算过滤（人均消费不超过预算的 60%，留空间给多个 POI）
        if poi.get("avg_cost", 0) > budget * 0.6:
            continue

        # 偏好匹配加分
        score = poi.get("rating", 0)
        if preferences:
            matched = len(set(preferences) & set(poi.get("tags", [])))
            score += matched * 0.5

        candidates.append((score, poi))

    # 按分数降序排列
    candidates.sort(key=lambda x: x[0], reverse=True)

    # 取前 max_pois * 2 个候选（给路线规划 agent 更多选择）
    selected = candidates[: max_pois * 2]

    result = []
    for _, poi in selected:
        result.append(
            POI(
                id=poi["id"],
                name=poi["name"],
                category=poi["category"],
                sub_category=poi.get("sub_category", ""),
                rating=poi.get("rating", 0),
                avg_cost=poi.get("avg_cost", 0),
                location=Location(**poi["location"]) if poi.get("location") else None,
                business_hours=poi.get("business_hours", ""),
            )
        )
    return result
