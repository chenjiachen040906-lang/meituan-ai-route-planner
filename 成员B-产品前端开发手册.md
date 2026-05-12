# 成员 B — 产品 / 前端开发手册

> 赛题：美团 AI Hackathon 2026 赛题五 · 本地路线智能规划
> 角色：模拟数据集 + 前端界面 + 交互设计 + 地图可视化

---

## 一、核心职责

1. 构造高质量模拟 POI 数据集
2. 搭建前端界面（输入、结果展示、交互调整）
3. 地图可视化展示路线
4. 产品体验打磨（动画、对比视图、异常提示）

---

## 二、技术栈

| 组件 | 选型 |
|------|------|
| 语言 | Python 3.11+ |
| 前端框架 | Streamlit（快速出活，和 Python 无缝集成） |
| 地图可视化 | Folium（嵌入 Streamlit）或 高德 JS API |
| 数据格式 | JSON（严格遵守成员 A 定义的接口格式） |
| 辅助 | Pandas（数据处理）、Plotly（时间轴/图表） |

---

## 三、接口约定（必须遵守）

### 3.1 路线生成请求（发给成员 A 的后端）

```
POST /api/generate-route
```

```json
{
    "user_input": "下午半天在三里屯附近逛逛",
    "constraints": {
        "time_budget": "半天",
        "start_time": "14:00",
        "budget_per_person": 200,
        "preferences": ["美食", "拍照"],
        "people_count": 2
    }
}
```

### 3.2 路线生成响应（前端接收并渲染）

```json
{
    "success": true,
    "route_name": "三里屯半日美食打卡线",
    "pois": [
        {
            "id": "poi_001",
            "name": "Moka Bros",
            "category": "餐饮",
            "sub_category": "西餐轻食",
            "rating": 4.7,
            "avg_cost": 85,
            "arrival_time": "14:00",
            "duration_minutes": 60,
            "stay_reason": "ins网红餐厅，环境出片",
            "location": {
                "lat": 39.9342,
                "lng": 116.4544,
                "address": "三里屯太古里南区"
            },
            "business_hours": "10:00-22:00"
        }
    ],
    "total_cost_per_person": 180,
    "total_duration_minutes": 225,
    "summary": "路线文字描述...",
    "ai_reasoning": "AI 推理过程..."
}
```

### 3.3 调整请求（发给成员 A 的后端）

```
POST /api/adjust-route
```

```json
{
    "original_route": { "..." },
    "user_feedback": "第二站换一个不用排队的",
    "constraints": { "..." }
}
```

---

## 四、模拟数据集设计

### 4.1 POI 数据结构

```json
{
    "id": "poi_001",
    "name": "Moka Bros",
    "category": "餐饮",
    "sub_category": "西餐轻食",
    "rating": 4.7,
    "avg_cost": 85,
    "location": {
        "lat": 39.9342,
        "lng": 116.4544,
        "address": "三里屯太古里南区12号楼"
    },
    "business_hours": "10:00-22:00",
    "tags": ["拍照", "轻食", "网红", "约会"],
    "ugc_highlights": [
        "环境很好适合拍照，光线超棒",
        "沙拉很新鲜，蛋白质碗推荐",
        "周末人多建议工作日来"
    ],
    "avg_wait_minutes": 15,
    "best_visit_time": "下午",
    "suitable_for": ["情侣", "朋友聚会", "独处"]
}
```

### 4.2 数据量要求

| 区域 | 餐饮 | 娱乐/文化 | 购物 | 合计 |
|------|------|----------|------|------|
| 三里屯 | 15 | 8 | 5 | 28 |
| 南锣鼓巷 | 12 | 10 | 5 | 27 |
| 王府井 | 10 | 8 | 8 | 26 |
| 望京 | 10 | 5 | 3 | 18 |
| 五道口 | 8 | 5 | 3 | 16 |
| **合计** | **55** | **36** | **24** | **115** |

### 4.3 数据构造要点

1. **真实性**：店名、地址、菜系要像真的（可以参考大众点评风格）
2. **多样性**：覆盖不同价位（人均 30-300）、不同类型、不同评分
3. **UGC 评价**：每个 POI 写 3-5 条真实感强的评价，突出特色
4. **标签体系**：统一标签（拍照、排队少、性价比高、约会、亲子、夜生活等）
5. **营业时间**：合理设置（餐厅 11:00-21:30，酒吧 18:00-02:00 等）
6. **地理坐标**：同一区域的 POI 坐标要合理，步行距离 5-15 分钟

### 4.4 数据文件结构

```
data/
├── pois.json              # 全部 POI 数据
├── areas.json             # 区域定义（名称 + 边界坐标）
└── sample_queries.json    # 示例用户输入（用于测试）
```

---

## 五、前端页面设计

### 5.1 页面布局（聊天式交互）

整体风格：类似 ChatGPT 的对话式界面，输入框固定在底部，上方滚动展示对话历史和路线结果。

```
┌─────────────────────────────────────────────────────┐
│  🗺️ AI 本地路线智能规划                              │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │              📋 约束条件栏（可折叠）              │ │
│  │  ⏰ 时间 [半天 ▾]  💰 人均 [200] 👥 人数 [2]    │ │
│  │  🏷️ 偏好 [美食] [拍照] [+添加]                  │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │              💬 对话记录区（可滚动）              │ │
│  │                                                   │ │
│  │  ┌───────────────────────────────────────────┐   │ │
│  │  │ 🧑 用户                                    │   │ │
│  │  │ 下午半天想在三里屯吃喝玩乐，人均200以内    │   │ │
│  │  └───────────────────────────────────────────┘   │ │
│  │                                                   │ │
│  │  ┌───────────────────────────────────────────┐   │ │
│  │  │ 🤖 AI 助手                                 │   │ │
│  │  │ 好的，为您规划了一条三里屯半日美食打卡线：   │   │ │
│  │  │                                             │   │ │
│  │  │ ┌──────────────────────────────────────┐   │   │ │
│  │  │ │ 🗺️ 路线地图（Folium）                 │   │   │ │
│  │  │ │   [POI 标记 + 路线连线]               │   │   │ │
│  │  │ └──────────────────────────────────────┘   │   │ │
│  │  │                                             │   │ │
│  │  │ ┌──────────────────────────────────────┐   │   │ │
│  │  │ │ 1. Moka Bros — 14:00 停留 60min      │   │   │ │
│  │  │ │    ⭐4.7 · 💰人均85 · 西餐轻食       │   │   │ │
│  │  │ │    > 环境出片，适合下午茶拍照          │   │   │ │
│  │  │ ├──────────────────────────────────────┤   │   │ │
│  │  │ │ 2. 三里屯太古里 — 15:15 停留 90min   │   │   │ │
│  │  │ │    ⭐4.5 · 免费 · 购物逛街            │   │   │ │
│  │  │ │    > 开放式街区，拍照圣地              │   │   │ │
│  │  │ ├──────────────────────────────────────┤   │   │ │
│  │  │ │ 3. 局气 — 17:00 停留 75min            │   │   │ │
│  │  │ │    ⭐4.6 · 💰人均95 · 北京菜          │   │   │ │
│  │  │ │    > 蜂窝煤炒饭必点，正宗北京味        │   │   │ │
│  │  │ └──────────────────────────────────────┘   │   │ │
│  │  │                                             │   │ │
│  │  │ 💰 人均约 180 元 · ⏱️ 总时长约 3.5 小时    │   │ │
│  │  └───────────────────────────────────────────┘   │ │
│  │                                                   │ │
│  │  ┌───────────────────────────────────────────┐   │ │
│  │  │ 🧑 用户                                    │   │ │
│  │  │ 第二站换一个不用排队的                      │   │ │
│  │  └───────────────────────────────────────────┘   │ │
│  │                                                   │ │
│  │  ┌───────────────────────────────────────────┐   │ │
│  │  │ 🤖 AI 助手                                 │   │ │
│  │  │ 已为您调整，将太古里替换为：                │   │ │
│  │  │ 2. 三里屯 Village — 15:15 停留 80min     │   │ │
│  │  │    ⭐4.4 · 免费 · 购物逛街                 │   │ │
│  │  │    > 人少清净，周末也不挤，适合闲逛        │   │ │
│  │  │ ⚠️ 路线已更新（第2站变更）                 │   │ │
│  │  └───────────────────────────────────────────┘   │ │
│  │                                                   │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │ 💬 描述你的出行想法...                [发送 ➤]  │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**布局要点：**

1. **顶部约束栏**：可折叠，默认收起只显示摘要标签（"半天 · 💰200 · 美食拍照"），点击展开编辑
2. **对话区**：占满中间空间，自动滚动到最新消息
3. **用户消息**：右对齐气泡，浅色背景
4. **AI 消息**：左对齐气泡，内嵌地图 + 路线卡片
5. **底部输入框**：固定在底部，单行输入，回车发送，支持 `Shift+回车` 换行
6. **路线调整时**：变更的 POI 用黄色高亮标注 diff

### 5.2 核心页面功能

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 自然语言输入 | P0 | 主输入框，支持自由描述 |
| 约束条件设置 | P0 | 时间、预算、人数、偏好的快捷选择 |
| 路线卡片展示 | P0 | 每个 POI 的详情卡片（时间、名称、理由、费用） |
| 地图路线展示 | P1 | Folium 地图 + POI 标记 + 路线连线 |
| 对话式调整 | P1 | 用户追问 → 重新生成 → 差异高亮 |
| 多方案对比 | P2 | 并排展示 2-3 条路线方案 |
| 时间轴视图 | P2 | 纵向时间轴展示行程安排 |

### 5.3 交互细节

1. **加载状态**：生成路线时显示 Agent 思考过程（"正在理解您的需求..." → "正在筛选合适的地点..." → "正在规划最优路线..."）
2. **调整高亮**：路线被修改的部分用黄色高亮显示
3. **POI 卡片点击**：点击展开详情（UGC 评价、营业时间、位置信息）
4. **地图交互**：hover POI 显示名称，点击跳转详情

---

## 六、开发计划

### Week 1（5.12 - 5.18）：数据 + 基础页面

| 天 | 任务 | 产出 |
|----|------|------|
| Day 1-2 | 构造三里屯区域的 POI 模拟数据（25+ 条） | `data/pois.json` 三里屯部分 |
| Day 3-4 | 搭 Streamlit 页面骨架 + 输入组件 | 页面能输入、能展示 mock 结果 |
| Day 5-6 | 补充南锣鼓巷、王府井数据 | 完成 80+ 条 POI |
| Day 7 | 和成员 A 联调，跑通第一个端到端流程 | 前后端对接成功 |

### Week 2（5.19 - 5.25）：体验打磨

| 天 | 任务 | 产出 |
|----|------|------|
| Day 1-2 | 实现路线卡片组件（带时间线样式） | 路线详情页 |
| Day 3-4 | 嵌入 Folium 地图 + 路线标记 | 地图可视化 |
| Day 5-6 | 实现对话式调整的 UI（追问区） | 交互闭环 |
| Day 7 | 补充望京、五道口数据，完成全部 115 条 | 数据集完成 |

### Week 3（5.26 - 6.7）：加分项 + 收尾

| 天 | 任务 | 产出 |
|----|------|------|
| Day 1-2 | 多方案对比视图 | 对比功能 |
| Day 3-4 | 动画效果 + 加载状态 + 异常提示 | 体验优化 |
| Day 5-6 | 写用户文档 + 录演示视频 | 文档素材 |
| Day 7 | 部署测试 + 最终打磨 | 上线就绪 |

---

## 七、Streamlit 骨架参考（聊天式交互）

```python
import streamlit as st
import requests

st.set_page_config(page_title="AI 本地路线规划", layout="wide")

# ========== 自定义样式 ==========
st.markdown("""
<style>
    /* 输入框固定在底部 */
    .stChatInput { position: fixed; bottom: 0; left: 0; right: 0; z-index: 999; }
    /* 路线卡片样式 */
    .route-card {
        border: 1px solid #e0e0e0; border-radius: 12px;
        padding: 12px 16px; margin: 8px 0;
    }
    .route-card:hover { background-color: #f8f9fa; }
    .poi-highlight { background-color: #fff3cd; padding: 2px 6px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

st.title("AI 本地路线智能规划")

# ========== 约束条件栏（折叠式） ==========
with st.expander("约束条件", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        time_budget = st.selectbox("时间", ["半天", "一天", "两天"])
        start_time = st.time_input("出发时间")
    with col2:
        budget = st.number_input("人均预算(元)", value=200, step=50)
        people = st.number_input("人数", value=2, min_value=1, max_value=10)
    with col3:
        preferences = st.multiselect("偏好", ["美食", "拍照", "户外", "文化", "购物", "亲子", "夜生活", "休闲"])

# 约束摘要标签
constraint_tags = f"⏰ {time_budget} · 💰 人均{budget}元 · 👥 {people}人"
if preferences:
    constraint_tags += f" · 🏷️ {'、'.join(preferences)}"
st.caption(constraint_tags)

# ========== 会话状态 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_route" not in st.session_state:
    st.session_state.current_route = None

# ========== 渲染历史消息 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)
        # 如果消息包含路线数据，渲染路线卡片
        if "route" in msg and msg["route"]:
            render_route_card(msg["route"])

# ========== 路线卡片渲染函数 ==========
def render_route_card(route, highlights=None):
    """渲染路线详情卡片"""
    # 地图（如果有坐标数据）
    if route.get("pois") and route["pois"][0].get("location"):
        try:
            import folium
            from streamlit_folium import st_folium
            m = folium.Map(location=[route["pois"][0]["location"]["lat"],
                                      route["pois"][0]["location"]["lng"]], zoom_start=14)
            coords = []
            for i, poi in enumerate(route["pois"]):
                lat, lng = poi["location"]["lat"], poi["location"]["lng"]
                folium.Marker([lat, lng], popup=f"{i+1}. {poi['name']}",
                              icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
                coords.append([lat, lng])
            folium.PolyLine(coords, color="blue", weight=3, opacity=0.7).add_to(m)
            st_folium(m, height=300, use_container_width=True)
        except ImportError:
            st.info("安装 streamlit-folium 以启用地图功能")

    # POI 列表
    for i, poi in enumerate(route["pois"]):
        is_highlight = highlights and poi["id"] in highlights
        css_class = "route-card poi-highlight" if is_highlight else "route-card"
        st.markdown(f"""
        <div class="{css_class}">
            <strong>{i+1}. {poi['name']}</strong> — {poi.get('arrival_time', '')} · 停留 {poi.get('duration_minutes', 60)}min<br>
            <small>{poi['category']} · {poi.get('sub_category', '')} · ⭐{poi.get('rating', '')} · 💰人均{poi.get('avg_cost', 0)}元</small><br>
            <em>> {poi.get('stay_reason', '')}</em>
        </div>
        """, unsafe_allow_html=True)

    # 路线总结
    st.markdown(f"**💰 人均约 {route.get('total_cost_per_person', 0)} 元** · "
                f"**⏱️ 总时长约 {route.get('total_duration_minutes', 0) // 60} 小时**")

# ========== 用户输入（底部） ==========
if prompt := st.chat_input("描述你的出行想法，比如：下午半天想在三里屯吃喝玩乐"):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 判断是初次请求还是追问调整
    with st.chat_message("assistant"):
        with st.spinner("AI 正在为您规划路线..."):
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
                    }
                }
                resp = requests.post("http://localhost:8000/api/adjust-route", json=payload)
            else:
                # 首次生成
                payload = {
                    "user_input": prompt,
                    "constraints": {
                        "time_budget": time_budget,
                        "start_time": str(start_time),
                        "budget_per_person": budget,
                        "preferences": preferences,
                        "people_count": people
                    }
                }
                resp = requests.post("http://localhost:8000/api/generate-route", json=payload)

            result = resp.json()

        if result.get("success"):
            route = result
            st.session_state.current_route = route
            summary = f"好的，为您规划了 **{route['route_name']}**：\n\n{route.get('summary', '')}"
            st.markdown(summary)
            render_route_card(route, highlights=route.get("changed_poi_ids"))
            st.session_state.messages.append({
                "role": "assistant",
                "content": summary,
                "route": route
            })
        else:
            error_msg = result.get("error", "路线生成失败，请重试")
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
```

---

## 八、数据构造示例

```json
{
    "id": "poi_sz_001",
    "name": "Moka Bros",
    "category": "餐饮",
    "sub_category": "西餐轻食",
    "rating": 4.7,
    "avg_cost": 85,
    "location": {
        "lat": 39.9342,
        "lng": 116.4544,
        "address": "朝阳区三里屯太古里南区S8-12"
    },
    "business_hours": "10:00-22:00",
    "tags": ["拍照", "轻食", "网红", "约会", "环境好"],
    "ugc_highlights": [
        "光线超棒，随便拍都出片",
        "蛋白质碗很好吃，健身人士友好",
        "周末人多，建议工作日下午来"
    ],
    "avg_wait_minutes": 20,
    "best_visit_time": "下午",
    "suitable_for": ["情侣", "朋友聚会", "独处"]
}
```

---

## 九、注意事项

1. **数据格式必须和成员 A 的接口一致**：字段名、嵌套结构不能改，改动前先沟通
2. **模拟数据要像真的**：店名、地址、评价要真实感强，评委看的是质量不是数量
3. **前端先用 mock 数据开发**：不要等成员 A 的后端，先用本地 JSON 模拟返回
4. **Streamlit 的 session_state**：对话历史、当前路线都要存，页面刷新不丢失
5. **地图性能**：POI 太多时只显示当前路线的标记，不要一次全画

---

## 十、每日同步

每天晚上花 10 分钟和成员 A 同步：
- 今天完成了什么
- 明天计划做什么
- 有没有接口格式需要调整
- 有没有阻塞项需要对方配合
- 数据进度是否满足联调需求
