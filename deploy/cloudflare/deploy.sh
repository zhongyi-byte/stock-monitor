#!/bin/bash
# Cloudflare 部署脚本

set -e

echo "🚀 开始部署股市监控系统到 Cloudflare"

# 检查 wrangler 是否安装
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler CLI 未安装，请先安装:"
    echo "npm install -g wrangler"
    exit 1
fi

# 检查是否已登录
if ! wrangler whoami &> /dev/null; then
    echo "🔐 请先登录 Cloudflare:"
    wrangler login
fi

echo "📁 切换到部署目录..."
cd "$(dirname "$0")"

# 创建 D1 数据库（如果不存在）
echo "🗄️  创建 D1 数据库..."
DATABASE_ID=$(wrangler d1 create stock-monitor-db --json | jq -r '.result.id')

if [ -z "$DATABASE_ID" ] || [ "$DATABASE_ID" = "null" ]; then
    echo "❌ 创建 D1 数据库失败"
    exit 1
fi

echo "✅ D1 数据库创建成功，ID: $DATABASE_ID"

# 更新 wrangler.toml 中的数据库 ID
sed -i.bak "s/database_id = \"\"/database_id = \"$DATABASE_ID\"/" wrangler.toml

# 初始化数据库表结构
echo "🔧 初始化数据库表结构..."
wrangler d1 execute stock-monitor-db --file=../sql/init.sql

# 设置环境变量（需要用户手动输入）
echo "🔑 设置环境变量..."
echo "请设置以下环境变量："

read -p "📧 发送者邮箱: " SENDER_EMAIL
read -s -p "🔐 邮箱密码/授权码: " EMAIL_PASSWORD
echo
read -p "📨 接收者邮箱: " RECIPIENT_EMAIL
read -p "🏷️  Cloudflare Account ID: " CF_ACCOUNT_ID
read -s -p "🔑 Cloudflare API Token: " CF_API_TOKEN
echo

# 设置 secrets
wrangler secret put EMAIL_PASSWORD <<< "$EMAIL_PASSWORD"
wrangler secret put CF_API_TOKEN <<< "$CF_API_TOKEN"
wrangler secret put SENDER_EMAIL <<< "$SENDER_EMAIL"
wrangler secret put RECIPIENT_EMAIL <<< "$RECIPIENT_EMAIL"
wrangler secret put CF_ACCOUNT_ID <<< "$CF_ACCOUNT_ID"
wrangler secret put CF_DATABASE_ID <<< "$DATABASE_ID"

# 部署 Worker
echo "🚀 部署 Worker..."
wrangler deploy

echo "✅ 部署完成！"
echo "🌐 Worker URL: https://stock-monitor-api.your-subdomain.workers.dev"
echo ""
echo "下一步："
echo "1. 部署前端到 Cloudflare Pages"
echo "2. 配置自定义域名（可选）"
echo "3. 测试 API 端点"