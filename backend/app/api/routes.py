from fastapi import APIRouter, HTTPException
from app.models.schemas import RouteRequest, RouteResponse, AdjustRequest
from app.agents.intent_agent import understand_intent
from app.agents.poi_agent import retrieve_pois
from app.agents.route_agent import plan_route

router = APIRouter(prefix="/api", tags=["route"])


@router.post("/generate-route", response_model=RouteResponse)
async def generate_route(req: RouteRequest):
    """根据用户输入生成路线方案。"""
    try:
        # Step 1: 理解用户意图
        intent = await understand_intent(req.user_input, req.constraints)

        # Step 2: 检索候选 POI
        candidates = retrieve_pois(intent)
        if not candidates:
            return RouteResponse(
                success=False,
                error="未找到符合条件的 POI，请尝试扩大范围或调整偏好",
            )

        # Step 3: 规划路线
        route = plan_route(intent, candidates)
        return route

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adjust-route", response_model=RouteResponse)
async def adjust_route(req: AdjustRequest):
    """根据用户反馈调整已有路线。"""
    try:
        # 把原始路线和用户反馈一起发给 LLM 重新规划
        intent = {
            "area": "",
            "time_budget": req.constraints.time_budget,
            "budget_per_person": req.constraints.budget_per_person,
            "preferences": req.constraints.preferences,
            "people_count": req.constraints.people_count,
            "original_route": req.original_route.model_dump(),
            "user_feedback": req.user_feedback,
        }

        # 用原始路线的 POI 作为候选池，加上用户反馈重新规划
        candidates = retrieve_pois(intent)
        if not candidates:
            # fallback: 用原始路线的 POI 作为候选
            candidates = req.original_route.pois

        route = plan_route(intent, candidates)

        # 标记变更的 POI（简单比较 id）
        old_ids = {p.id for p in req.original_route.pois}
        route.changed_poi_ids = [p.id for p in route.pois if p.id not in old_ids]

        return route

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pois")
async def list_pois(category: str = "", area: str = "", max_cost: int = 9999):
    """查询 POI 列表（调试用）。"""
    from app.agents.poi_agent import _load_pois

    all_pois = _load_pois()
    filtered = all_pois

    if category:
        filtered = [p for p in filtered if category in p.get("category", "")]
    if area:
        filtered = [p for p in filtered if area in p.get("location", {}).get("address", "")]
    if max_cost < 9999:
        filtered = [p for p in filtered if p.get("avg_cost", 0) <= max_cost]

    return {"pois": filtered, "total": len(filtered)}
