# 股市监控系统部署指南

本系统采用解耦架构设计，支持多种部署方式。业务逻辑与部署环境完全分离，可以轻松在不同平台间迁移。

## 🏗️ 架构设计

### 核心组件解耦

- **数据层**: 数据库适配器模式，支持 SQLite ↔ Cloudflare D1 无缝切换
- **配置层**: 统一配置管理，支持文件配置 + 环境变量
- **业务逻辑**: 完全独立，不依赖部署环境
- **前端**: Vue.js + Tailwind CSS，可部署到任何静态托管

### 支持的部署方式

| 部署方式 | 数据库 | 前端 | 后端 | 定时任务 | 成本 |
|---------|--------|------|------|---------|-----|
| 本地Mac mini | SQLite | 本地Flask | Flask | Cron/手动 | 免费 |
| Cloudflare | D1 | Pages | Workers | Cron Triggers | 免费额度大 |
| Docker | SQLite/PostgreSQL | Nginx | Flask | Docker Cron | VPS费用 |
| VPS | SQLite/MySQL | Nginx | Gunicorn | Systemd Timer | $5-10/月 |

## 🚀 Cloudflare 部署

### 前置要求

1. Cloudflare 账户
2. 安装 Node.js 和 npm
3. 安装 Wrangler CLI: `npm install -g wrangler`

### 自动部署

```bash
cd deploy/cloudflare
./deploy.sh
```

### 手动部署步骤

#### 1. 创建 D1 数据库

```bash
wrangler d1 create stock-monitor-db
```

记录返回的 database_id，更新 `wrangler.toml`：

```toml
[[d1_databases]]
binding = "DB"
database_name = "stock-monitor-db"
database_id = "your-database-id-here"
```

#### 2. 初始化数据库

```bash
wrangler d1 execute stock-monitor-db --file=../sql/init.sql
```

#### 3. 设置环境变量

```bash
wrangler secret put EMAIL_PASSWORD
wrangler secret put SENDER_EMAIL  
wrangler secret put RECIPIENT_EMAIL
wrangler secret put CF_API_TOKEN
wrangler secret put CF_ACCOUNT_ID
wrangler secret put CF_DATABASE_ID
```

#### 4. 部署后端 Worker

```bash
wrangler deploy
```

#### 5. 部署前端到 Pages

```bash
# 1. 构建前端资源
cd ../../web
# 复制静态文件到 Pages 项目

# 2. 通过 Cloudflare Dashboard 创建 Pages 项目
# 3. 连接 GitHub 仓库，设置构建命令
```

### 配置域名

1. 在 Cloudflare Dashboard 中设置自定义域名
2. 更新前端 API 地址指向你的 Worker 域名

## 🏠 本地部署（Mac mini）

### 保持现有方式

系统已完全兼容现有的本地部署方式：

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置邮件
python main.py --setup

# 添加策略
python main.py --add-strategy

# 启动Web界面
python main.py --web

# 启动监控
python main.py --start
```

### 配置文件示例

本地部署使用 `config.json`：

```json
{
  "database": {
    "type": "sqlite",
    "path": "stock_monitor.db"
  },
  "deployment": {
    "type": "local",
    "environment": "development"
  }
}
```

## 🐳 Docker 部署

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "main.py", "--web", "--port", "5000"]
```

### docker-compose.yml

```yaml
version: '3.8'
services:
  stock-monitor:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - DB_TYPE=sqlite
      - DB_PATH=/app/data/stock_monitor.db
```

## ⚙️ 配置管理

### 配置优先级

1. **环境变量** (最高优先级)
2. **配置文件** (config.json)
3. **默认值** (最低优先级)

### 环境变量列表

| 变量名 | 说明 | 示例 |
|-------|------|------|
| `DB_TYPE` | 数据库类型 | `sqlite`, `cloudflare_d1` |
| `DB_PATH` | SQLite路径 | `stock_monitor.db` |
| `CF_DATABASE_ID` | D1数据库ID | `xxx-xxx-xxx` |
| `CF_ACCOUNT_ID` | Cloudflare账户ID | `xxx-xxx-xxx` |
| `CF_API_TOKEN` | Cloudflare API令牌 | `xxx-xxx-xxx` |
| `EMAIL_ENABLED` | 启用邮件 | `true`, `false` |
| `SENDER_EMAIL` | 发送邮箱 | `your@gmail.com` |
| `EMAIL_PASSWORD` | 邮箱密码 | `your-app-password` |
| `RECIPIENT_EMAIL` | 接收邮箱 | `notify@example.com` |
| `DEPLOYMENT_TYPE` | 部署类型 | `local`, `cloudflare` |
| `ENVIRONMENT` | 环境 | `development`, `production` |

## 🔄 部署迁移

### 从本地迁移到Cloudflare

1. **导出数据**:
   ```bash
   sqlite3 stock_monitor.db .dump > backup.sql
   ```

2. **转换数据**:
   ```bash
   # 清理SQLite特定语法，转换为标准SQL
   sed 's/AUTOINCREMENT/AUTO_INCREMENT/g' backup.sql > d1_backup.sql
   ```

3. **导入到D1**:
   ```bash
   wrangler d1 execute stock-monitor-db --file=d1_backup.sql
   ```

4. **更新配置**:
   ```bash
   export DB_TYPE=cloudflare_d1
   export DEPLOYMENT_TYPE=cloudflare
   ```

### 从Cloudflare迁移到本地

1. **导出D1数据**:
   ```bash
   wrangler d1 export stock-monitor-db --output=backup.sql
   ```

2. **导入SQLite**:
   ```bash
   sqlite3 stock_monitor.db < backup.sql
   ```

3. **更新配置**:
   ```json
   {
     "database": {"type": "sqlite"},
     "deployment": {"type": "local"}
   }
   ```

## 🔍 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查环境变量配置
   - 验证API令牌权限

2. **API调用超时**
   - 检查网络连接
   - 验证股票API可用性

3. **邮件发送失败**
   - 检查SMTP配置
   - 验证应用密码

### 日志调试

```bash
# 本地调试
python main.py --run-once --debug

# Cloudflare调试
wrangler tail stock-monitor-api
```

## 📊 监控和维护

### 健康检查

- 本地: `http://localhost:5000/api/stats`
- Cloudflare: `https://your-worker.workers.dev/api/stats`

### 定期维护

1. **备份数据库** (每周)
2. **检查API配额** (每月)
3. **更新依赖包** (每季度)
4. **测试邮件通知** (每月)

---

## 🎯 下一步

选择你的部署方式并按照对应的步骤进行部署。如果需要Cloudflare相关工具支持，请告知具体需求。