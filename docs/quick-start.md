# 快速启动指南

## 🎯 目标

在10分钟内启动并运行自主规划平台。

## 📋 前置要求

- Python 3.11+
- Docker Desktop
- Git

## 🚀 快速启动

### 1. 克隆项目

```bash
git clone <repository-url>
cd agent-platform
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API Keys
# OPENAI_API_KEY=your-key
# ANTHROPIC_API_KEY=your-key
```

### 3. 启动基础设施

**Windows (PowerShell):**
```powershell
.\scripts\start-dev.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

### 4. 启动控制平面

打开新终端:

```bash
cd control-plane
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8080
```

### 5. 启动认知平面

打开新终端:

```bash
cd cognition-plane
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## ✅ 验证安装

访问以下地址验证服务是否正常运行：

- **控制平面 API 文档**: http://localhost:8080/docs
- **认知平面 API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8080/health

## 🧪 测试 API

### 使用 Swagger UI

1. 打开 http://localhost:8080/docs
2. 点击 `/api/v1/auth/register` 注册用户
3. 点击 `/api/v1/auth/login` 登录获取 Token
4. 点击右上角 "Authorize" 按钮，输入 Token
5. 测试其他 API

### 使用 cURL

#### 1. 注册用户

```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

#### 2. 登录

```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

保存返回的 `access_token`。

#### 3. 创建会话

```bash
TOKEN="your-access-token"

curl -X POST http://localhost:8080/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Session",
    "model": "gpt-4o"
  }'
```

#### 4. 发送消息

```bash
SESSION_ID="your-session-id"

curl -X POST "http://localhost:8080/api/v1/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, can you help me with a math problem?"
  }'
```

#### 5. 监听事件流

```bash
RUN_ID="your-run-id"

curl -N http://localhost:8080/api/v1/runs/$RUN_ID/stream \
  -H "Authorization: Bearer $TOKEN"
```

## 🛠️ 开发工具

### 运行测试

```bash
# 控制平面测试
cd control-plane
pytest tests/ -v

# 认知平面测试
cd cognition-plane
pytest tests/ -v
```

### 代码格式化

```bash
# 安装开发工具
pip install black isort mypy

# 格式化代码
black app/
isort app/

# 类型检查
mypy app/
```

### 数据库迁移

```bash
cd control-plane

# 创建新迁移
alembic revision --autogenerate -m "description of changes"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 🐛 常见问题

### 1. 数据库连接失败

**问题**: `connection refused` 错误

**解决**:
```bash
# 检查 PostgreSQL 是否运行
docker ps | grep postgres

# 重启 PostgreSQL
docker-compose restart postgres
```

### 2. Redis 连接失败

**问题**: Redis 连接错误

**解决**:
```bash
# 检查 Redis 是否运行
docker ps | grep redis

# 测试 Redis 连接
docker exec -it agent-platform-redis redis-cli ping
```

### 3. API Key 错误

**问题**: LLM 调用失败

**解决**:
- 检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确
- 确保你有足够的 API 额度

### 4. 端口被占用

**问题**: 端口 8080 或 8000 已被占用

**解决**:
```bash
# 查找占用端口的进程
# Windows
netstat -ano | findstr :8080

# Linux/Mac
lsof -i :8080

# 杀死进程或更改应用端口
uvicorn app.main:app --port 8081
```

## 📚 下一步

- 📖 阅读 [API 文档](./docs/api.md)
- 🏗️ 了解 [架构设计](./架构设计文档.md)
- 🛠️ 学习如何 [添加自定义工具](./docs/custom-tools.md)
- 🎨 开发 [前端界面](./frontend/README.md)

## 💡 提示

- 生产环境务必修改 `SECRET_KEY`
- 使用环境变量管理敏感信息
- 定期备份数据库
- 监控服务日志和指标

## 🆘 获取帮助

- 📖 查看文档
- 🐛 提交 Issue
- 💬 加入社区讨论

祝你开发愉快！🎉
