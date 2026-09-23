# 自主规划平台 (Autonomous Planning Platform)

一个具备自主规划能力的AI平台，能够理解用户意图，自主分解复杂任务，调用工具和技能，实现智能化的任务执行和问题解决。

## 🚀 核心特性

- ✅ **自主规划**: 将复杂任务分解为可执行的子任务
- ✅ **工具编排**: 智能选择和调用工具完成任务
- ✅ **过程可视化**: 实时展示Agent的思考、行动、观察过程
- ✅ **人机协作**: 支持Human-in-the-Loop，关键决策需人工确认
- ✅ **可扩展**: 支持自定义工具和技能的快速集成

## 📋 技术栈

### 后端
- **Python 3.11+** - 统一后端技术栈
- **FastAPI** - 高性能异步Web框架
- **LangGraph** - Agent工作流引擎
- **PostgreSQL** - 主数据库
- **Redis** - 缓存和流式状态
- **RabbitMQ** - 消息队列

### 前端
- **React 19** - UI框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **shadcn/ui** - UI组件库

## 🏗️ 项目结构

```
.
├── control-plane/          # 控制平面（会话管理、认证、事件持久化）
│   ├── app/
│   ├── tests/
│   └── requirements.txt
│
├── cognition-plane/        # 认知平面（Agent引擎、工具调用）
│   ├── app/
│   ├── tests/
│   └── requirements.txt
│
├── shared/                 # 共享代码（模型、Schema、工具）
│   ├── models/
│   ├── schemas/
│   └── utils/
│
├── frontend/               # React前端
│   ├── src/
│   └── package.json
│
├── docs/                   # 文档
├── scripts/                # 脚本工具
└── docker-compose.yml      # Docker编排
```

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd agent-platform
```

### 2. 启动基础设施
```bash
docker-compose up -d postgres redis rabbitmq
```

### 3. 启动后端服务

#### 控制平面
```bash
cd control-plane
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8080
```

#### 认知平面
```bash
cd cognition-plane
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. 启动前端
```bash
cd frontend
npm install
npm run dev
```

### 5. 访问应用
- 前端: http://localhost:5173
- 控制平面API: http://localhost:8080/docs
- 认知平面API: http://localhost:8000/docs

## 📖 文档

- [架构设计文档](./架构设计文档.md)
- [Python后端架构总结](./Python后端架构总结.md)
- [API文档](./docs/api.md)

## 🧪 测试

```bash
# 控制平面测试
cd control-plane
pytest tests/ -v --cov=app

# 认知平面测试
cd cognition-plane
pytest tests/ -v --cov=app
```

## 📝 开发指南

### 代码风格
```bash
# 格式化代码
black app/
isort app/

# 类型检查
mypy app/
```

### 数据库迁移
```bash
# 创建迁移
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📧 联系方式

- 项目维护: Agent Platform Team
- Email: support@agent-platform.com
