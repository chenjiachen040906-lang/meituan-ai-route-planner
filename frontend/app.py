"""
AI 本地路线智能规划 - 前端应用
Streamlit 聊天式交互界面
"""
import streamlit as st
import requests
from datetime import time
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="AI 本地路线智能规划", layout="wide", page_icon="🗺️")

# ========== 自定义样式 ==========
st.markdown("""
<style>
    /* 路线卡片样式 */
    .route-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
        background-color: #fafafa;
    }
    .route-card:hover {
        background-color: #f0f0f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* POI 高亮样式（用于调整后的变更标注） */
    .poi-highlight {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 12px;
    }

    /* 对话气泡样式 */
    .user-bubble {
        background-color: #e3f2fd;
        padding: 10px 16px;
        border-radius: 12px 12px 0 12px;
        margin-left: auto;
        max-width: 80%;
    }

    .ai-bubble {
        background-color: #f5f5f5;
        padding: 10px 16px;
        border-radius: 12px 12px 12px 0;
        margin-right: auto;
        max-width: 90%;
    }

    /* 时间标签样式 */
    .time-tag {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: bold;
    }

    /* 评分星星 */
    .rating {
        color: #ffc107;
    }

    /* 预算标签 */
    .cost-tag {
        color: #ff5722;
    }
</style>
""", unsafe_allow_html=True)

st.title("🗺️ AI 本地路线智能规划")

# ========== 约束条件栏（折叠式） ==========
with st.expander("⚙️ 约束条件", expanded=False):
    col1, col2, col3 = st.columns(3)

    with col1:
        # 时间预算区域
        st.subheader("⏰ 时间预算", help="选择您出行的时间段")

        # 时段选择（多选）
        time_periods = st.multiselect(
            "时段选择",
            ["早上 (6:00-12:00)", "下午 (12:00-18:00)", "晚上 (18:00-24:00)"],
            default=["下午 (12:00-18:00)"],
            key="time_periods"
        )

        # 一整天复选框
        all_day = st.checkbox("一整天", key="all_day", help="勾选后自动覆盖时段选择")

        # 自定义时间区域
        st.markdown("**自定义时间**（优先级最高）")
        custom_col1, custom_col2, custom_col3 = st.columns([2, 1, 2])
        with custom_col1:
            custom_start = st.time_input("开始时间", value=None, key="custom_start")
        with custom_col2:
            st.write("")
            st.markdown("<div style='text-align: center; padding-top: 25px;'>至</div>", unsafe_allow_html=True)
        with custom_col3:
            custom_end = st.time_input("结束时间", value=None, key="custom_end")

    with col2:
        # 出发地点
        st.subheader("🚩 出发地点")

        # 搜索回调：触发地理编码
        def _on_location_change():
            st.session_state._geo_trigger = True

        start_location = st.text_input(
            "出发地点",
            placeholder="例如：三里屯太古里",
            key="start_location",
            on_change=_on_location_change,
        )

        # 搜索按钮（点击也触发）
        search_clicked = st.button("🔍 搜索地点", key="search_location")

        # 当回车（on_change）或点击按钮时执行地理编码
        if start_location and (search_clicked or st.session_state.get("_geo_trigger")):
            st.session_state._geo_trigger = False
            with st.spinner("正在搜索位置..."):
                try:
                    geo_url = "https://nominatim.openstreetmap.org/search"
                    geo_resp = requests.get(
                        geo_url,
                        params={"q": start_location, "format": "json", "limit": 1},
                        headers={"User-Agent": "AI-Route-Planner/1.0"},
                        timeout=10,
                    )
                    geo_data = geo_resp.json()
                    if geo_data:
                        lat = float(geo_data[0]["lat"])
                        lon = float(geo_data[0]["lon"])
                        st.session_state.map_lat = lat
                        st.session_state.map_lng = lon
                        st.session_state.map_address = geo_data[0].get("display_name", start_location)
                        st.session_state.map_searched = True
                    else:
                        st.warning("⚠️ 未找到该位置，请检查输入后重试")
                        st.session_state.map_searched = True
                except requests.exceptions.Timeout:
                    st.warning("⚠️ 搜索超时，请稍后重试")
                except Exception as e:
                    st.warning(f"⚠️ 搜索失败：{e}")

        # 地图展示区域
        _map_lat = st.session_state.get("map_lat", 39.9342)
        _map_lng = st.session_state.get("map_lng", 116.4544)
        _map_zoom = 16 if st.session_state.get("map_searched") else 14

        _m = folium.Map(location=[_map_lat, _map_lng], zoom_start=_map_zoom, height=300)

        # 仅在成功搜索到位置时添加红色标记
        if st.session_state.get("map_lat") and st.session_state.get("map_searched"):
            folium.Marker(
                [_map_lat, _map_lng],
                popup=st.session_state.get("map_address", start_location),
                tooltip="🚩 出发地点",
                icon=folium.Icon(color="red", icon="map-marker"),
            ).add_to(_m)

        st_folium(_m, height=300, use_container_width=True, key="start_location_map")

        budget = st.number_input("人均预算(元)", value=200, min_value=0, step=50)

    with col3:
        people = st.number_input("人数", value=2, min_value=1, max_value=10)
        preferences = st.multiselect(
            "偏好",
            ["美食", "拍照", "户外", "文化", "购物", "亲子", "夜生活", "休闲"],
            default=["美食"]
        )

# 根据优先级规则确定 time_budget 值
# 优先级：自定义时间 > 一整天 > 时段选择 > 默认
if custom_start and custom_end:
    # 自定义时间优先级最高
    time_budget = f"{custom_start.strftime('%H:%M')}-{custom_end.strftime('%H:%M')}"
elif all_day:
    time_budget = "一整天"
elif time_periods:
    # 简化标签，移除时间范围显示
    simplified_periods = [p.split(" ")[0] for p in time_periods]
    time_budget = "+".join(simplified_periods)
else:
    time_budget = "下午"  # 默认值

# 约束摘要标签
constraint_tags = f"⏰ {time_budget} · 💰 人均{budget}元 · 👥 {people}人"
if preferences:
    constraint_tags += f" · 🏷️ {'、'.join(preferences)}"
if start_location:
    constraint_tags += f" · 🚩 {start_location}"
st.caption(constraint_tags)

# ========== 会话状态 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_route" not in st.session_state:
    st.session_state.current_route = None

# ========== 路线卡片渲染函数 ==========
def render_route_card(route, highlights=None):
    """渲染路线详情卡片"""
    # 地图（如果有坐标数据）
    if route.get("pois") and route["pois"][0].get("location"):
        try:

            # 计算地图中心点
            avg_lat = sum(p["location"]["lat"] for p in route["pois"]) / len(route["pois"])
            avg_lng = sum(p["location"]["lng"] for p in route["pois"]) / len(route["pois"])

            m = folium.Map(location=[avg_lat, avg_lng], zoom_start=14)
            coords = []

            for i, poi in enumerate(route["pois"]):
                lat, lng = poi["location"]["lat"], poi["location"]["lng"]
                popup_content = f"""
                <b>{i+1}. {poi['name']}</b><br>
                {poi['category']} · ⭐{poi.get('rating', 0)}<br>
                💰人均{poi.get('avg_cost', 0)}元<br>
                📍{poi['location'].get('address', '')}
                """
                folium.Marker(
                    [lat, lng],
                    popup=popup_content,
                    tooltip=f"{i+1}. {poi['name']}",
                    icon=folium.Icon(color="red", icon="info-sign")
                ).add_to(m)
                coords.append([lat, lng])

            # 绘制路线连线
            if len(coords) > 1:
                folium.PolyLine(coords, color="blue", weight=3, opacity=0.7).add_to(m)

            st_folium(m, height=300, use_container_width=True)
        except ImportError:
            st.info("💡 安装 `streamlit-folium` 以启用地图功能：`pip install streamlit-folium`")
        except Exception as e:
            st.warning(f"地图渲染失败：{str(e)}")

    # 路线名称
    if route.get("route_name"):
        st.markdown(f"### 📌 {route['route_name']}")

    # POI 列表
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

    # 路线总结
    total_cost = route.get("total_cost_per_person", 0)
    total_duration = route.get("total_duration_minutes", 0)
    hours = total_duration // 60
    minutes = total_duration % 60

    st.markdown(f"**💰 人均约 {total_cost} 元** · **⏱️ 总时长约 {hours} 小时 {minutes} 分钟**")

    # AI 推理过程（可选显示）
    if route.get("ai_reasoning"):
        with st.expander("🤔 AI 规划思路"):
            st.markdown(route["ai_reasoning"])

# ========== 渲染历史消息 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # 渲染文本内容
        if msg.get("content"):
            st.markdown(msg["content"])

        # 渲染路线卡片
        if "route" in msg and msg["route"]:
            render_route_card(msg["route"], highlights=msg.get("highlights"))

# ========== API 请求函数 ==========
@st.cache_data(ttl=60)
def call_api(endpoint, payload):
    """调用后端 API"""
    try:
        resp = requests.post(
            f"http://localhost:8000{endpoint}",
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "无法连接到后端服务，请确保后端服务正在运行"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "请求超时，请稍后重试"}
    except Exception as e:
        return {"success": False, "error": f"请求失败：{str(e)}"}

# ========== 用户输入（底部） ==========
if prompt := st.chat_input("描述你的出行想法，比如：下午半天想在三里屯吃喝玩乐"):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 判断是初次请求还是追问调整
    with st.chat_message("assistant"):
        with st.spinner("🤔 AI 正在为您规划路线..."):
            if st.session_state.current_route:
                # 追问调整
                payload = {
                    "original_route": st.session_state.current_route,
                    "user_feedback": prompt,
                    "constraints": {
                        "time_budget": time_budget,
                        "budget_per_person": budget,
                        "preferences": preferences,
                        "people_count": people
                    },
                    "start_location": start_location if start_location else None
                }
                result = call_api("/api/adjust-route", payload)
            else:
                # 首次生成
                payload = {
                    "user_input": prompt,
                    "constraints": {
                        "time_budget": time_budget,
                        "budget_per_person": budget,
                        "preferences": preferences,
                        "people_count": people
                    },
                    "start_location": start_location if start_location else None
                }
                result = call_api("/api/generate-route", payload)

        # 处理结果
        if result.get("success"):
            route = result
            st.session_state.current_route = route

            # 构建回复文本
            summary = f"好的，为您规划了 **{route['route_name']}**："
            if route.get("summary"):
                summary += f"\n\n{route['summary']}"

            st.markdown(summary)

            # 渲染路线卡片（获取变更高亮）
            highlights = route.get("changed_poi_ids")
            render_route_card(route, highlights=highlights)

            # 保存到会话
            st.session_state.messages.append({
                "role": "assistant",
                "content": summary,
                "route": route,
                "highlights": highlights
            })
        else:
            error_msg = result.get("error", "路线生成失败，请重试")
            st.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ {error_msg}"
            })

# ========== 侧边栏信息 ==========
with st.sidebar:
    st.header("📌 使用说明")
    st.markdown("""
    1. **设置约束条件**：点击顶部的「约束条件」展开面板
    2. **描述出行需求**：在底部输入框自然语言描述
    3. **查看路线**：AI 生成路线后展示地图和 POI 卡片
    4. **调整路线**：可针对已生成的路线提出修改意见

    **示例输入：**
    - 下午半天在三里屯附近逛逛，人均200以内
    - 两个朋友去南锣鼓巷，想找拍照好看的地方
    - 周末一家三口去王府井，需要有适合孩子的项目
    """)

    st.divider()

    st.header("🔧 后端状态")
    try:
        resp = requests.get("http://localhost:8000/health", timeout=2)
        if resp.status_code == 200:
            st.success("✅ 后端服务运行中")
        else:
            st.warning("⚠️ 后端服务异常")
    except:
        st.error("❌ 无法连接到后端服务")
        st.caption("请先启动后端：")
        st.code("cd backend\nuvicorn app.main:app --reload", language="bash")