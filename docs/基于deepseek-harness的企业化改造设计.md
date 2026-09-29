# auto_react_aigc 基于 deepseek-harness 的企业化改造设计文档

> 版本：v1.0（设计稿，未实施）
> 日期：2026-09-28
> 目标：保留现有 React 企业级配置 UI + control-plane 后端，将 Agent 运行底座从
> 手写 LangGraph ReAct 替换为 deepseek-harness（dsh），实现"自主规划 + 提示词
> + Skill + 知识库 + 多模型"可配置的企业级 Agent 平台。

---

## 1. 现状盘点（基于代码实证）

### 1.1 你已有的资产（评估：成熟度高，应保留）

| 层 | 现状 | 代码位置 |
|---|---|---|
| **前端** | 企业级 Agent 配置台：模型/提示词/知识库/本体/Skill/工具六类可配 + 右侧对话调试面板 | `frontend/src/pages/agents/config.tsx`（AgentConfig） |
| **资源池** | 5 类资源（kb/skill/prompt/ontology/ds/tool）统一 CRUD，Skill 带文件树 | `control-plane/app/services/resource_service.py` |
| **Agent 管理** | CRUD + 状态机（draft→published→archived，版本快照） | `control-plane/app/services/agent_service.py` |
| **运行契约** | `compile_runspec()` 已把 Agent 配置编译为 **RunSpec**（配置态→运行态） | `control-plane/app/services/agent_service.py` + `shared/schemas/runspec.py` |
| **会话/消息/运行** | SSE 实时事件流、事件持久化重放 | `control-plane/app/services/` |

### 1.2 你的瓶颈（评估：需要替换的部分）

| 瓶颈 | 具体表现 |
|---|---|
| **执行引擎弱** | `cognition-plane` 是手写 LangGraph ReAct：schema 硬编码、无 skill 加载、无知识库检索、工具池写死 |
| **配置没真正驱动运行** | RunSpec 编译出来了，但 cognition 侧只会简单 ReAct，六类能力几乎没被真正使用 |
| **知识库/本体缺实现** | UI 有挂载入口，后端无检索/语义引擎 |

### 1.3 关键判断

> **你的 UI + control-plane 已经"长成了"企业级 Agent 平台的配置与管理层，
> 缺的只是"能真正自主规划的执行内核"。** deepseek-harness 正是这个内核。

---

## 2. deepseek-harness 能力边界（已验证）

| 你的配置项 | harness 原生支持 | 映射方式 |
|---|---|---|
| 模型选择 | ✅ 原生多模型路由 | providers 配置（OpenAI 兼容/DeepSeek/自定义） |
| 系统提示词 | ✅ 原生 system-prompt 插件 | 可直接注入 |
| **Skill** | ✅ 原生 skill 系统 | `.dsh/skills` 目录 + `ctx.skills` 注册，**与你的 Skill 概念一一对应** |
| 工具 | ✅ 原生工具注册表 | `ctx.tools.register(defineTool(...))`，与你的 tool 池对应 |
| **知识库 (kb)** | ⚠️ 无内置 RAG/向量检索 | 需自建检索，以自定义工具形式接入（`tool_kb_search`） |
| **本体 (ontology)** | ❌ 无本体引擎 | 降级为"文档注入提示词"，或未来接知识图谱 |
| **自主规划** | ✅ 原生 agent loop + plan 插件 | 比手写 ReAct 强，支持多步自主规划 |
| **企业集成** | ✅ **headless profile**：`dsh --profile headless "任务"` | 无 UI 执行任务，适合 API 化后端 |

### 2.1 关键技术点：headless + patch = 企业后端的运行时

```sh
# 无 UI 执行一次任务（企业后端的 API 化执行入口）
dsh --profile headless "帮我查 Ada 的订单并统计金额"
```

`--patch` 机制可动态注入配置层（模型、提示词、skill、工具注册），这是把
**RunSpec 翻译成 harness 可执行配置**的桥梁：

```yaml
# runspec.patch.yml —— 由 control-plane 根据 RunSpec 动态生成
- insert:
    - id: llm-provider
      name: '@deepseek-ai/dsh-llm-deepseek'   # 或自定义 provider
      config:
        model: Qwen3.5-397b-a17b
        apiKey: ${AIMP_OPENAI_API_KEY}
    - id: business-tools
      name: 'D:/path/to/business-tools.ts'    # 你的业务工具插件
    - id: kb-retrieval
      name: 'D:/path/to/kb-retrieval.ts'      # 知识库检索工具
```

---

## 3. 目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端 React UI (保留)                       │
│  AgentConfig(六类配置)  资源池页(资源/管理)  对话调试面板        │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST / SSE
┌──────────────────────────────▼──────────────────────────────┐
│                  control-plane (保留，增强)                   │
│  AgentService.compile_runspec() → RunSpec                    │
│  + 新增: HarnessAdapter（翻译 RunSpec → patch 配置）          │
│  + 新增: 会话/运行事件桥（SSE → harness 输出）                 │
└──────────────────────────────┬──────────────────────────────┘
                               │ 生成 patch yml + 发起 headless 任务
┌──────────────────────────────▼──────────────────────────────┐
│              deepseek-harness (dsh) 运行时【替换 cognition】 │
│  headless profile + --patch 注入                              │
│   ├─ 模型路由 (多模型)                                        │
│   ├─ 系统提示词 (可引用资源)                                  │
│   ├─ Skill 系统 (自动装载你配置的 skills)                     │
│   ├─ 工具注册表 (业务工具 + kb 检索工具)                      │
│   └─ 自主规划 loop (plan + agent loop)                        │
└──────────────────────────────────────────────────────────────┘
```

### 3.1 关键设计决策

1. **保留**：React UI、control-plane、数据库、资源池、RunSpec 契约
2. **替换**：cognition-plane 的 LangGraph ReAct → harness headless profile
3. **新增**：`HarnessAdapter`（control-plane 内新增服务），职责：
   - RunSpec → `cordis.patch.yml`（模型/提示词/skills/tools/kb 映射）
   - 调用 `dsh --profile headless --patch <生成配置> "<用户消息>"`
   - 把 harness 输出（最终答案 + 会话日志）翻译回现有 SSE 事件流
4. **渐进式**：先跑通"模型+提示词+工具"，再逐步接 Skill、知识库

---

## 4. RunSpec → harness 配置映射表

| RunSpec 字段 | harness 映射 |
|---|---|
| `model` | llm-provider 插件 `config.model` |
| `system_prompt` | system-prompt 插件配置 / 会话首条 system 消息 |
| `tools[]` | 动态加载对应工具插件（业务工具名 → 插件路径映射表） |
| `skills[]` | `ctx.skills.register()` 或 `.dsh/skills/` 目录 |
| `knowledge[]` | kb 检索工具插件配置（resource_id → 检索后端） |
| `temperature` | llm-provider `config.temperature` |
| `max_iterations` | plan/agent-loop 插件配置 |
| `timeout` | headless 调用超时包装 |

---

## 5. 知识库（kb）接入方案（harness 无原生 RAG）

**原则：知识库不内置，用"自定义工具"接入。**

```
方案 A（推荐）：向量检索工具
  kb 资源上传 → 切片 → embedding（调你的 Qwen/DeepSeek embed API）
             → 存入向量库（chroma/pgvector/milvus）
  自定义工具 tool_kb_search(resource_id, query, top_k)
  → 检索结果作为工具输出喂给 agent 增强回答（RAG）

方案 B（轻量）：文档注入
  kb 资源 → 在 system prompt 中注入文档摘要/全文（适合小文档）
  实现成本最低，但受上下文限制
```

---

## 6. 实施路线（分阶段，每阶段可验证）

### Phase 0：环境验证（✅ 已完成 2026-09-28）
- ✅ 确认 harness headless profile 可运行任务（`dsh --profile headless "任务"`）
- ✅ 验证 `--patch` 注入自定义模型 provider 生效
- ✅ **成功接入企业模型 AIMP Qwen**（`qwen3-5-397b-a17b`，OpenAI 兼容端点）
- ✅ 验证自主规划（模型自行判断是否调用工具）
- 验证产物：`docs/aimp-llm.patch.yml`（AIMP provider + 默认模型配置）
- 实测输出示例：
  - `"用一句话自我介绍"` → 模型认知自身是 qwen3-5 驱动的 harness 智能体
  - `"1+2*3 等于多少"` → 自主推理输出 `7`，自行判断无需工具

### Phase 1：核心打通（模型 + 提示词 + 工具）
- control-plane 新增 `HarnessAdapter`
- RunSpec → patch 配置生成器
- headless 调用 + 事件桥（harness 输出 → SSE）
- ✅ 验收：UI 里配置一个 Agent（选模型、填提示词、挂工具），
  右侧调试面板能通过 harness 真实回答

### Phase 2：Skill 接入
- RunSpec.skills → harness skill 注册
- ✅ 验收：UI 挂载的 Skill 能真实影响 Agent 行为

### Phase 3：知识库接入
- 选型方案 A 或 B，实现 kb 检索工具
- ✅ 验收：UI 挂载知识库后，Agent 能基于知识库回答

### Phase 4：企业化收尾
- 本体降级方案（文档注入）或独立知识图谱选型
- 多模型路由完整接入（Qwen/DeepSeek/Claude/gpt-4o 各 provider）
- 会话持久化、事件重放、版本管理的完整打通

---

## 7. 风险与权衡

| 风险 | 说明 | 缓解 |
|---|---|---|
| harness 是开发者预览 | README 明示将有不兼容变更 | 锁定版本（当前 0.1.7-rc.1），harness 封装在 Adapter 层隔离 |
| headless 是进程级调用 | 每次任务起进程，并发/性能需评估 | 首版验证可行性；后续可上 sdk profile（常驻 JSON-RPC） |
| 知识库无原生支持 | 需自建检索 | 方案 A 成本可控，或先方案 B 验证价值 |
| 本体无引擎 | 只能降级 | 明确告知用户，避免过度承诺 |
| Node 运行时依赖 | 企业环境需部署 Node 24+ | Docker 化，与现有容器编排并存 |

---

## 8. 与"直接重写进 harness Web UI"的对比

| 维度 | 保留 UI + harness 内核（本方案） | 迁进 harness Web UI |
|---|---|---|
| 前端定制（本体/知识库交互） | ✅ 完全保留 | ❌ 受限于 harness 自带 UI |
| 改动量 | 中（新增 Adapter 层） | 大（重写前端 + 数据模型） |
| 企业集成（已有 auth/权限/数据库） | ✅ 复用 | 需重接 |
| 自主规划能力 | ✅ 同源 harness | ✅ |
| **结论** | **推荐** | 不推荐 |

---

## 9. 下一步行动（待你确认后启动）

1. 确认本设计文档方向
2. Phase 0 环境验证（需要 harness 环境，可在当前已装的 deepseek-harness 上做）
3. 需要你提供：企业实际使用的模型 API Key（或确认用 DeepSeek 官方 key）
