"""
数据存储模块 - 使用适配器模式支持多种数据库
"""

from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from .database_adapter import DatabaseAdapter, SQLiteAdapter


class Database:
    def __init__(self, adapter: DatabaseAdapter = None, db_path: str = "stock_monitor.db"):
        """
        数据库类 - 使用适配器模式支持多种数据库
        
        Args:
            adapter: 数据库适配器实例，如果为None则使用SQLite
            db_path: SQLite数据库路径（仅当adapter为None时使用）
        """
        if adapter is None:
            self.adapter = SQLiteAdapter(db_path)
        else:
            self.adapter = adapter
            
        self.adapter.connect()
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        self.adapter.init_tables()
    
    def add_strategy(self, name: str, symbol: str, condition_type: str, 
                    target_price: float, action: str = 'notify') -> int:
        """添加监控策略"""
        return self.adapter.add_strategy(name, symbol, condition_type, target_price, action)
    
    def get_active_strategies(self) -> List[Dict]:
        """获取所有活跃的监控策略"""
        return self.adapter.get_active_strategies()
    
    def trigger_strategy(self, strategy_id: int):
        """标记策略为已触发"""
        self.adapter.trigger_strategy(strategy_id)
    
    def save_price(self, price_data: Dict):
        """保存价格数据"""
        self.adapter.save_price(price_data)
    
    def add_notification(self, strategy_id: int, message: str):
        """记录通知"""
        self.adapter.add_notification(strategy_id, message)
    
    def get_strategies_summary(self) -> Dict:
        """获取策略统计信息"""
        return self.adapter.get_strategies_summary()
    
    def get_recent_notifications(self, limit: int = 20) -> List[Dict]:
        """获取最近的通知记录"""
        return self.adapter.get_recent_notifications(limit)
    
    def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """获取最新价格 - 兼容性方法"""
        # 这个方法在当前架构中不常用，但保留用于向后兼容
        # 实际价格获取通过DataFetcher实时获取
        return None


if __name__ == "__main__":
    # 测试数据存储模块
    print("=== 数据存储模块测试 ===")
    
    # 创建数据库实例
    db = Database(db_path="test_stock_monitor.db")
    
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
    
    # 测试策略统计
    print("\n4. 策略统计:")
    summary = db.get_strategies_summary()
    print(f"   总策略: {summary['total']}, 活跃: {summary['active']}, 已触发: {summary['triggered']}")
    
    print("\n✅ 数据存储模块测试完成！")
    
    # 清理测试文件
    Path("test_stock_monitor.db").unlink(missing_ok=True)