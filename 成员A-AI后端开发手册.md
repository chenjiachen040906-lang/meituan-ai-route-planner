# 成员 A — AI / 后端开发手册

> 赛题：美团 AI Hackathon 2026 赛题五 · 本地路线智能规划
> 角色：AI Agent 架构 + 后端服务 + 路线生成逻辑

---

## 一、核心职责

1. 搭建 Multi-Agent 架构，实现完整的路线生成流程
2. 对接 LLM API，编写 Prompt 工程
3. 实现约束过滤与路线优化逻辑
4. 提供稳定的后端 API 供前端调用

---

## 二、技术栈

| 组件 | 选型 |
|------|------|
| 语言 | Python 3.11+ |
| LLM | Claude API (Anthropic SDK) 或 OpenAI API |
| Agent 框架 | LangGraph（或自建轻量 Agent，不超过 200 行） |
| 后端框架 | FastAPI |
| 路线优化 | LLM + 规则约束（不上 TSP，用 LLM 做启发式排序） |

---

## 三、接口约定（必须遵守）

### 3.1 路线生成请求

```
POST /api/generate-route
Content-Type: application/json
```

```json
{
    "user_input": "下午半天在三里屯附近逛逛，想吃点好的拍拍照",
    "constraints": {
        "time_budget": "半天",
        "start_time": "14:00",
        "budget_per_person": 200,
        "preferences": ["美食", "拍照"],
        "people_count": 2
    }
}
```

### 3.2 路线生成响应

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
            "stay_reason": "ins网红餐厅，环境出片，适合下午茶",
            "location": {
                "lat": 39.9342,
                "lng": 116.4544,
                "address": "三里屯太古里南区"
            },
            "business_hours": "10:00-22:00"
        },
        {
            "id": "poi_002",
            "name": "三里屯太古里",
            "category": "娱乐",
            "sub_category": "购物逛街",
            "rating": 4.5,
            "avg_cost": 0,
            "arrival_time": "15:15",
            "duration_minutes": 90,
            "stay_reason": "开放式街区，拍照圣地，各类潮牌聚集",
            "location": {
                "lat": 39.9338,
                "lng": 116.4550,
                "address": "三里屯太古里"
            },
            "business_hours": "10:00-22:00"
        },
        {
            "id": "poi_003",
            "name": "局气",
            "category": "餐饮",
            "sub_category": "北京菜",
            "rating": 4.6,
            "avg_cost": 95,
            "arrival_time": "17:00",
            "duration_minutes": 75,
            "stay_reason": "正宗北京菜，蜂窝煤炒饭必点，适合聚餐",
            "location": {
                "lat": 39.9350,
                "lng": 116.4530,
                "address": "三里屯路19号"
            },
            "business_hours": "11:00-21:30"
        }
    ],
    "total_cost_per_person": 180,
    "total_duration_minutes": 225,
    "summary": "下午从三里屯出发，先在 Moka Bros 喝个下午茶拍照，然后逛太古里街区，傍晚去局气吃正宗北京菜，全程步行可达，人均不到 200。",
    "ai_reasoning": "根据用户偏好'美食+拍照'，选择了高颜值餐厅和开放式街区..."
}
```

### 3.3 路线调整请求

```
POST /api/adjust-route
Content-Type: application/json
```

```json
{
    "original_route": { "...上一次返回的完整路线..." },
    "user_feedback": "第二站换一个不用排队的，预算不变",
    "constraints": {
        "time_budget": "半天",
        "budget_per_person": 200
    }
}
```

### 3.4 POI 数据查询（供调试用）

```
GET /api/pois?category=餐饮&area=三里屯&max_cost=100
```

```json
{
    "pois": [
        {
            "id": "poi_001",
            "name": "...",
            "category": "餐饮",
            "sub_category": "...",
            "rating": 4.7,
            "avg_cost": 85,
            "location": { "lat": 39.93, "lng": 116.45 },
            "business_hours": "10:00-22:00",
            "tags": ["拍照", "轻食", "网红"],
            "ugc_highlights": ["环境很好适合拍照", "沙拉很新鲜"]
        }
    ],
    "total": 12
}
```

---

## 四、开发计划

### Week 1（5.12 - 5.18）：跑通核心流程

| 天 | 任务 | 产出 |
|----|------|------|
| Day 1-2 | 搭建项目骨架 + FastAPI 服务 | `/api/generate-route` 返回 mock 数据 |
| Day 3-4 | 实现意图理解 Agent（从自然语言提取结构化信息） | Prompt + 解析逻辑 |
| Day 5-6 | 实现 POI 筛选 + 路线排序 Agent | 核心 Agent 链路跑通 |
| Day 7 | 用成员 B 的模拟数据联调 | 端到端生成第一条真实路线 |

### Week 2（5.19 - 5.25）：打磨质量

| 天 | 任务 | 产出 |
|----|------|------|
| Day 1-2 | 加约束过滤逻辑（时间、预算、营业时间冲突检测） | 约束系统 |
| Day 3-4 | 实现 `/api/adjust-route` 对话式调整 | 支持追问修改 |
| Day 5-6 | Prompt 调优 + 多方案生成（省钱/品质/打卡） | 三种风格路线 |
| Day 7 | 性能优化，确保 < 10 秒响应 | 达标 |

### Week 3（5.26 - 6.7）：加分项 + 收尾

| 天 | 任务 | 产出 |
|----|------|------|
| Day 1-3 | 用户偏好记忆（简单的 session 内偏好学习） | 个性化能力 |
| Day 4-5 | 异常处理 + 边界 case 兜底 | 健壮性 |
| Day 6-7 | 部署 + 写技术文档 | 上线 |

---

## 五、Agent 设计参考

### 5.1 整体流程

```
用户输入
    ↓
[Intent Agent] → { area, time, budget, preferences, people }
    ↓
[POI Retrieval Agent] → 候选 POI 列表（已过滤）
    ↓
[Route Planner Agent] → 排序 + 时间分配 + 约束校验
    ↓
[Response Agent] → 结构化路线 + 自然语言摘要
```

### 5.2 Intent Agent Prompt 骨架

```
你是一个出行意图理解助手。从用户的自然语言输入中提取结构化信息。

用户输入：{user_input}

请提取以下字段：
- area: 目标区域/地点
- time_budget: 时间预算（半天/一天/两天/具体小时数）
- start_time: 预计出发时间
- budget_per_person: 人均预算（元）
- preferences: 偏好标签列表（从以下选择：美食, 拍照, 户外, 文化, 购物, 亲子, 夜生活, 休闲）
- people_count: 人数
- special_requirements: 特殊要求（如有）

输出 JSON 格式。
```

### 5.3 Route Planner Agent Prompt 骨架

```
你是一个本地路线规划专家。根据用户意图和候选 POI 列表，规划一条最优路线。

用户意图：{intent}
候选 POI：{candidate_pois}
约束条件：{constraints}

规划要求：
1. 路线必须考虑地理距离，减少来回折返
2. 餐饮类 POI 安排在合理的用餐时间段
3. 每个 POI 的停留时间要合理
4. 检查营业时间是否冲突
5. 总预算不能超标
6. 给出每个 POI 的选择理由（结合 UGC 评价）

输出结构化 JSON 路线方案。
```

---

## 六、注意事项

1. **先跑通再优化**：第一周目标是端到端跑通，不要纠结 Prompt 完美度
2. **接口格式严格遵守**：前端依赖这个格式，改动必须提前沟通
3. **LLM 输出要兜底**：模型返回的 JSON 可能格式不对，加 try-except 和重试
4. **性能关注点**：POI 数据量大时先在本地做过滤再送 LLM，别把几百条 POI 全塞进 prompt
5. **和成员 B 约定**：模拟数据的字段名必须和接口格式一致，用 `id` 做关联

---

## 七、每日同步

每天晚上花 10 分钟和成员 B 同步：
- 今天完成了什么
- 明天计划做什么
- 有没有接口变更需要通知对方
- 有没有阻塞项需要对方配合
