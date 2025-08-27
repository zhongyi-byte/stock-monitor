# 股市监控系统

一个简单易用的股市监控应用，支持港股、美股和比特币价格监控。当价格触发设定条件时自动发送邮件通知。

## 功能特点

- 🎯 **多市场支持**: 美股、港股、比特币
- 📧 **邮件通知**: 自动发送触发提醒邮件  
- 🕐 **定时监控**: 每天定时自动检查
- 💾 **数据存储**: SQLite数据库存储策略和历史
- 🔧 **易于配置**: 命令行交互式设置
- 🌐 **Web界面**: 可视化管理和监控面板

## 快速开始

### 1. 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖包
pip install -r requirements.txt
```

### 2. 配置邮件服务
```bash
python main.py --setup
```
按提示配置邮箱信息（支持Gmail、QQ邮箱、163邮箱等）

### 3. 添加监控策略
```bash
python main.py --add-strategy
```

示例策略：
- **苹果低价买入**: AAPL 价格低于 $170 时买入提醒
- **腾讯突破新高**: 0700.HK 价格高于 HKD 350 时通知
- **比特币回调**: BTC 价格低于 $60,000 时买入提醒

### 4. 启动系统

#### 🌐 Web界面管理（推荐）
```bash
# 启动Web管理界面
python main.py --web

# 浏览器访问 http://127.0.0.1:5000
# 可以查看实时统计、策略列表、通知历史
```

#### 🖥️ 命令行监控
```bash
# 启动后台监控系统
python main.py --start
```

## 使用说明

### 命令行选项

```bash
python main.py --help                # 显示帮助信息
python main.py --setup              # 邮件配置向导
python main.py --add-strategy       # 添加监控策略
python main.py --list-strategies    # 查看所有策略
python main.py --run-once           # 手动执行一次检查
python main.py --start              # 启动监控系统
python main.py --web                # 启动Web管理界面
python main.py --web --port 8080    # 指定Web端口
```

### 📱 Web界面功能

- **📊 实时统计面板**: 显示总策略数、活跃策略、已触发数量、监控股票数
- **📈 策略管理**: 查看所有当前监控策略，显示触发条件和动作类型
- **📧 通知历史**: 查看所有邮件通知记录，按时间排序
- **🔄 自动刷新**: 每分钟自动刷新数据，保持信息实时性
- **📱 响应式设计**: 支持手机和桌面设备访问

### 🎯 完整使用流程

1. **首次设置**:
   ```bash
   source venv/bin/activate
   python main.py --setup              # 配置邮箱
   python main.py --add-strategy       # 添加策略
   ```

2. **查看和管理**:
   ```bash
   python main.py --web                # 启动Web界面
   # 浏览器访问 http://127.0.0.1:5000
   ```

3. **后台监控**:
   ```bash
   python main.py --start              # 启动定时监控
   ```

### 支持的股票代码

**美股**:
- AAPL (苹果)
- MSFT (微软) 
- GOOGL (谷歌)
- TSLA (特斯拉)

**港股**:
- 0700.HK (腾讯控股)
- 0941.HK (中国移动)
- 2318.HK (中国平安)

**加密货币**:
- BTC (比特币)

### 监控条件

- **below**: 价格低于目标值时触发
- **above**: 价格高于目标值时触发

### 触发动作

- **notify**: 仅通知
- **buy**: 买入提醒  
- **sell**: 卖出提醒

## 邮件配置说明

### Gmail配置
1. 开启两步验证
2. 生成应用专用密码
3. 使用应用专用密码而非普通密码
4. SMTP服务器: `smtp.gmail.com`

### QQ邮箱配置
1. 在邮箱设置中开启SMTP服务
2. 获取授权码
3. 使用授权码而非QQ密码
4. SMTP服务器: `smtp.qq.com`

## 配置文件

系统会自动创建 `config.json` 配置文件：

```json
{
  "db_path": "stock_monitor.db",
  "schedule_time": "09:00",
  "test_mode": false,
  "email": {
    "enabled": true,
    "sender_email": "your-email@gmail.com",
    "password": "your-app-password",
    "recipient_email": "notify@example.com",
    "smtp_server": "smtp.gmail.com"
  }
}
```

## 项目结构

```
stock_monitor/
├── main.py              # 主程序入口（支持Web模式）
├── config.json         # 配置文件
├── stock_monitor.db    # SQLite数据库
├── requirements.txt    # Python依赖
├── demo_setup.py       # 演示数据设置
├── data/
│   ├── fetcher.py      # 数据获取模块
│   └── storage.py      # 数据存储模块
├── strategy/
│   └── manager.py      # 策略管理模块
├── notification/
│   └── email_service.py # 邮件通知模块
├── monitor/
│   └── engine.py       # 监控引擎
└── web/
    ├── server.py       # Flask Web服务器
    └── templates/
        └── index.html  # Web界面模板
```

## 使用示例

### 添加策略示例

```bash
$ python main.py --add-strategy

📈 添加监控策略
策略名称: 苹果低价买入机会
股票/币种代码: AAPL
选择条件 (1-2): 1
目标价格: 170
选择动作 (1-3): 2
✅ 策略创建成功! ID: 1
```

### 查看策略

```bash
$ python main.py --list-strategies

📊 当前监控策略
总策略: 2, 活跃: 2, 已触发: 0

活跃策略列表:
1. 苹果低价买入机会
   股票: AAPL | 触发条件: 价格低于 170.0 | 动作: buy
   创建时间: 2025-08-27 20:30:15
```

### 手动检查

```bash
$ python main.py --run-once

🔍 开始监控检查 - 2025-08-27 20:30:30
📊 当前活跃策略: 2 个
🚨 策略触发: 苹果低价买入机会
   Apple Inc. 当前价格: USD 175.84
   触发条件: below 170.0
📧 成功发送 1/1 个邮件通知
```

## 注意事项

- ⚠️ **投资风险**: 本系统仅供参考，请理性投资，注意风险控制
- 🌐 **网络依赖**: 需要稳定的网络连接获取股价数据
- 📧 **邮件限制**: 部分邮件服务商有发送频率限制
- 🔒 **密码安全**: 建议使用应用专用密码而非主密码

## 许可证

本项目仅供学习和个人使用。