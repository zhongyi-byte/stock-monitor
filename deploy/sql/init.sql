-- D1 数据库初始化SQL
-- 创建股市监控系统所需的表结构

-- 策略表
CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    condition_type TEXT NOT NULL,
    target_price REAL NOT NULL,
    action TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP
);

-- 价格数据表
CREATE TABLE IF NOT EXISTS price_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 通知记录表
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES strategies (id)
);

-- 创建索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);
CREATE INDEX IF NOT EXISTS idx_strategies_symbol ON strategies(symbol);
CREATE INDEX IF NOT EXISTS idx_price_data_symbol ON price_data(symbol);
CREATE INDEX IF NOT EXISTS idx_price_data_timestamp ON price_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications(sent_at);