import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class Database:
    def __init__(self, db_path: str = "stock_monitor.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 监控策略表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    condition_type TEXT NOT NULL,  -- 'below', 'above'
                    target_price REAL NOT NULL,
                    action TEXT NOT NULL,          -- 'buy', 'sell', 'notify'
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    triggered_at TIMESTAMP NULL
                )
            ''')
            
            # 价格历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT NOT NULL,
                    name TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 通知记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id INTEGER,
                    message TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (strategy_id) REFERENCES strategies (id)
                )
            ''')
            
            conn.commit()
    
    def add_strategy(self, name: str, symbol: str, condition_type: str, 
                    target_price: float, action: str = 'notify') -> int:
        """添加监控策略"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO strategies (name, symbol, condition_type, target_price, action)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, symbol, condition_type, target_price, action))
            conn.commit()
            return cursor.lastrowid
    
    def get_active_strategies(self) -> List[Dict]:
        """获取所有活跃的监控策略"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, symbol, condition_type, target_price, action, created_at
                FROM strategies 
                WHERE is_active = 1 AND triggered_at IS NULL
            ''')
            
            columns = [desc[0] for desc in cursor.description]
            strategies = []
            for row in cursor.fetchall():
                strategy = dict(zip(columns, row))
                strategies.append(strategy)
            
            return strategies
    
    def trigger_strategy(self, strategy_id: int):
        """标记策略为已触发"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE strategies 
                SET triggered_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (strategy_id,))
            conn.commit()
    
    def save_price(self, price_data: Dict):
        """保存价格数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO price_history (symbol, price, currency, name)
                VALUES (?, ?, ?, ?)
            ''', (price_data['symbol'], price_data['price'], 
                  price_data['currency'], price_data['name']))
            conn.commit()
    
    def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """获取最新价格"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT symbol, price, currency, name, timestamp
                FROM price_history 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (symbol,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'symbol': row[0],
                    'price': row[1],
                    'currency': row[2],
                    'name': row[3],
                    'timestamp': row[4]
                }
            return None
    
    def add_notification(self, strategy_id: int, message: str):
        """记录通知"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notifications (strategy_id, message)
                VALUES (?, ?)
            ''', (strategy_id, message))
            conn.commit()
    
    def get_strategies_summary(self) -> Dict:
        """获取策略统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 总策略数
            cursor.execute('SELECT COUNT(*) FROM strategies')
            total = cursor.fetchone()[0]
            
            # 活跃策略数
            cursor.execute('SELECT COUNT(*) FROM strategies WHERE is_active = 1 AND triggered_at IS NULL')
            active = cursor.fetchone()[0]
            
            # 已触发策略数
            cursor.execute('SELECT COUNT(*) FROM strategies WHERE triggered_at IS NOT NULL')
            triggered = cursor.fetchone()[0]
            
            return {
                'total': total,
                'active': active,
                'triggered': triggered
            }


if __name__ == "__main__":
    # 测试数据存储模块
    print("=== 数据存储模块测试 ===")
    
    # 创建数据库实例
    db = Database("test_stock_monitor.db")
    
    # 测试添加策略
    print("\n1. 添加监控策略:")
    strategy_id1 = db.add_strategy("苹果低价买入", "AAPL", "below", 170.0, "buy")
    strategy_id2 = db.add_strategy("腾讯高价提醒", "0700.HK", "above", 350.0, "notify")
    strategy_id3 = db.add_strategy("比特币突破", "BTC", "above", 65000.0, "notify")
    
    print(f"   添加了3个策略，ID分别为: {strategy_id1}, {strategy_id2}, {strategy_id3}")
    
    # 测试获取策略
    print("\n2. 查看活跃策略:")
    strategies = db.get_active_strategies()
    for s in strategies:
        print(f"   {s['name']}: {s['symbol']} {s['condition_type']} {s['target_price']}")
    
    # 测试保存价格数据
    print("\n3. 保存价格数据:")
    test_price_data = [
        {'symbol': 'AAPL', 'price': 175.84, 'currency': 'USD', 'name': 'Apple Inc.'},
        {'symbol': '0700.HK', 'price': 320.50, 'currency': 'HKD', 'name': '腾讯控股'},
        {'symbol': 'BTC', 'price': 64250.0, 'currency': 'USD', 'name': 'Bitcoin'}
    ]
    
    for price_data in test_price_data:
        db.save_price(price_data)
        print(f"   保存 {price_data['name']}: {price_data['currency']} {price_data['price']}")
    
    # 测试获取最新价格
    print("\n4. 获取最新价格:")
    for symbol in ['AAPL', '0700.HK', 'BTC']:
        latest = db.get_latest_price(symbol)
        if latest:
            print(f"   {latest['name']}: {latest['currency']} {latest['price']}")
    
    # 测试策略统计
    print("\n5. 策略统计:")
    summary = db.get_strategies_summary()
    print(f"   总策略: {summary['total']}, 活跃: {summary['active']}, 已触发: {summary['triggered']}")
    
    print("\n✅ 数据存储模块测试完成！")
    
    # 清理测试文件
    Path("test_stock_monitor.db").unlink(missing_ok=True)