"""
前端工具函数
- render_route_card: 路线卡片 + 地图渲染
- geocode_location: 地理编码（地址 → 坐标）
"""
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium


def geocode_location(address: str, timeout: int = 10) -> dict | None:
    """调用 Nominatim 免费 API 将地址转为坐标。

    Returns:
        成功时返回 {"lat": float, "lng": float, "display_name": str}，
        未找到或请求失败时返回 None。
    """
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "AI-Route-Planner/1.0"},
            timeout=timeout,
        )
        data = resp.json()
        if data:
            return {
                "lat": float(data[0]["lat"]),
                "lng": float(data[0]["lon"]),
                "display_name": data[0].get("display_name", address),
            }
        return None
    except Exception:
        return None


def render_location_map(address: str) -> None:
    """在出发地点下方渲染可交互地图。

    用户点击「搜索地点」后调用此函数：执行地理编码并在地图上添加标记。
    坐标结果存入 st.session_state（map_lat / map_lng / map_address）。
    """
    result = geocode_location(address)
    if result:
        st.session_state.map_lat = result["lat"]
        st.session_state.map_lng = result["lng"]
        st.session_state.map_address = result["display_name"]
        st.session_state.map_searched = True
    else:
        st.warning("⚠️ 未找到该位置，请检查输入后重试")
        st.session_state.map_searched = True

    _render_map_widget()


def _render_map_widget() -> None:
    """渲染出发地点地图组件（带/不带标记）。"""
    lat = st.session_state.get("map_lat", 39.9342)
    lng = st.session_state.get("map_lng", 116.4544)
    zoom = 16 if st.session_state.get("map_searched") else 14

    m = folium.Map(location=[lat, lng], zoom_start=zoom, height=300)

    if st.session_state.get("map_lat") and st.session_state.get("map_searched"):
        folium.Marker(
            [lat, lng],
            popup=st.session_state.get("map_address", ""),
            tooltip="🚩 出发地点",
            icon=folium.Icon(color="red", icon="map-marker"),
        ).add_to(m)

    st_folium(m, height=300, use_container_width=True, key="start_location_map")


def render_route_card(route: dict, highlights: list | None = None) -> None:
    """渲染路线详情卡片（地图 + POI 列表 + 总结）。

    Args:
        route: 符合后端 RouteResponse 格式的字典。
        highlights: 需要高亮的 POI id 列表（用于调整后标注变更）。
    """
    # —— 地图 ——
    if route.get("pois") and route["pois"][0].get("location"):
        try:
            avg_lat = sum(p["location"]["lat"] for p in route["pois"]) / len(route["pois"])
            avg_lng = sum(p["location"]["lng"] for p in route["pois"]) / len(route["pois"])

            m = folium.Map(location=[avg_lat, avg_lng], zoom_start=14)
            coords = []

            for i, poi in enumerate(route["pois"]):
                lat, lng = poi["location"]["lat"], poi["location"]["lng"]
                popup_content = (
                    f"<b>{i+1}. {poi['name']}</b><br>"
                    f"{poi['category']} · ⭐{poi.get('rating', 0)}<br>"
                    f"💰人均{poi.get('avg_cost', 0)}元<br>"
                    f"📍{poi['location'].get('address', '')}"
                )
                folium.Marker(
                    [lat, lng],
                    popup=popup_content,
                    tooltip=f"{i+1}. {poi['name']}",
                    icon=folium.Icon(color="red", icon="info-sign"),
                ).add_to(m)
                coords.append([lat, lng])

            if len(coords) > 1:
                folium.PolyLine(coords, color="blue", weight=3, opacity=0.7).add_to(m)

            st_folium(m, height=300, use_container_width=True, key="route_map")
        except ImportError:
            st.info("💡 安装 `streamlit-folium` 以启用地图功能：`pip install streamlit-folium`")
        except Exception as e:
            st.warning(f"地图渲染失败：{e}")

    # —— 路线名称 ——
    if route.get("route_name"):
        st.markdown(f"### 📌 {route['route_name']}")

    # —— POI 列表 ——
    for i, poi in enumerate(route["pois"]):
        is_highlight = highlights and poi["id"] in highlights
        css_class = "poi-highlight" if is_highlight else "route-card"

        stay_reason = poi.get("stay_reason", "")
        rating = poi.get("rating", 0)
        avg_cost = poi.get("avg_cost", 0)
        arrival_time = poi.get("arrival_time", "--:--")
        duration = poi.get("duration_minutes", 60)

        card_html = f"""
        <div class="{css_class}">
            <strong>{i+1}. {poi['name']}</strong> — <span class="time-tag">{arrival_time}</span> · 停留 {duration}min<br>
            <small>{poi['category']} · {poi.get('sub_category', '')} · <span class="rating">⭐{rating}</span> · <span class="cost-tag">💰人均{avg_cost}元</span></small><br>
            <em>> {stay_reason}</em>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

    # —— 路线总结 ——
    total_cost = route.get("total_cost_per_person", 0)
    total_duration = route.get("total_duration_minutes", 0)
    hours = total_duration // 60
    minutes = total_duration % 60
    st.markdown(f"**💰 人均约 {total_cost} 元** · **⏱️ 总时长约 {hours} 小时 {minutes} 分钟**")

    # —— AI 推理过程 ——
    if route.get("ai_reasoning"):
        with st.expander("🤔 AI 规划思路"):
            st.markdown(route["ai_reasoning"])
