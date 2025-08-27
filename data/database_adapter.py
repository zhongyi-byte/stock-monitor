"""
数据库适配器接口 - 支持多种数据库后端
支持SQLite (本地) 和 Cloudflare D1 (云端)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import os


class DatabaseAdapter(ABC):
    """数据库适配器基类"""
    
    @abstractmethod
    def connect(self) -> None:
        """建立数据库连接"""
        pass
    
    @abstractmethod
    def init_tables(self) -> None:
        """初始化数据库表结构"""
        pass
    
    @abstractmethod
    def add_strategy(self, name: str, symbol: str, condition_type: str, 
                    target_price: float, action: str) -> int:
        """添加监控策略"""
        pass
    
    @abstractmethod
    def get_active_strategies(self) -> List[Dict]:
        """获取所有活跃策略"""
        pass
    
    @abstractmethod
    def trigger_strategy(self, strategy_id: int) -> None:
        """标记策略为已触发"""
        pass
    
    @abstractmethod
    def get_strategies_summary(self) -> Dict:
        """获取策略统计摘要"""
        pass
    
    @abstractmethod
    def save_price(self, price_data: Dict) -> None:
        """保存价格数据"""
        pass
    
    @abstractmethod
    def add_notification(self, strategy_id: int, message: str) -> None:
        """添加通知记录"""
        pass
    
    @abstractmethod
    def get_recent_notifications(self, limit: int = 20) -> List[Dict]:
        """获取最近的通知记录"""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite数据库适配器 - 用于本地部署"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = None
        
    def connect(self) -> None:
        """建立SQLite连接"""
        import sqlite3
        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        
    def init_tables(self) -> None:
        """初始化SQLite表结构"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 策略表
            cursor.execute('''
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
                )
            ''')
            
            # 价格数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
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
                    target_price: float, action: str) -> int:
        """添加监控策略"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO strategies (name, symbol, condition_type, target_price, action)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, symbol, condition_type, target_price, action))
            
            return cursor.lastrowid
    
    def get_active_strategies(self) -> List[Dict]:
        """获取所有活跃策略"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM strategies 
                WHERE status = 'active' 
                ORDER BY created_at DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def trigger_strategy(self, strategy_id: int) -> None:
        """标记策略为已触发"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE strategies 
                SET status = 'triggered', triggered_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (strategy_id,))
    
    def get_strategies_summary(self) -> Dict:
        """获取策略统计摘要"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                    COUNT(CASE WHEN status = 'triggered' THEN 1 END) as triggered
                FROM strategies
            ''')
            
            row = cursor.fetchone()
            return {
                'total': row[0],
                'active': row[1], 
                'triggered': row[2]
            }
    
    def save_price(self, price_data: Dict) -> None:
        """保存价格数据"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO price_data (symbol, price, currency, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                price_data['symbol'],
                price_data['price'],
                price_data.get('currency', 'USD'),
                price_data.get('timestamp', None)
            ))
    
    def add_notification(self, strategy_id: int, message: str) -> None:
        """添加通知记录"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notifications (strategy_id, message)
                VALUES (?, ?)
            ''', (strategy_id, message))
    
    def get_recent_notifications(self, limit: int = 20) -> List[Dict]:
        """获取最近的通知记录"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT n.message, n.sent_at, s.name as strategy_name
                FROM notifications n
                LEFT JOIN strategies s ON n.strategy_id = s.id
                ORDER BY n.sent_at DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]


class CloudflareD1Adapter(DatabaseAdapter):
    """Cloudflare D1 数据库适配器 - 用于云端部署"""
    
    def __init__(self, database_id: str, account_id: str, api_token: str):
        self.database_id = database_id
        self.account_id = account_id  
        self.api_token = api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}"
    
    def connect(self) -> None:
        """D1 连接验证"""
        # D1 是 HTTP API，无需持久连接
        pass
    
    def _execute_query(self, sql: str, params: List[Any] = None) -> Dict:
        """执行 D1 SQL 查询"""
        import requests
        
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'sql': sql,
            'params': params or []
        }
        
        response = requests.post(f"{self.base_url}/query", headers=headers, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def init_tables(self) -> None:
        """初始化 D1 表结构"""
        # 策略表
        self._execute_query('''
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
            )
        ''')
        
        # 价格数据表
        self._execute_query('''
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 通知记录表
        self._execute_query('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER,
                message TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies (id)
            )
        ''')
    
    def add_strategy(self, name: str, symbol: str, condition_type: str, 
                    target_price: float, action: str) -> int:
        """添加监控策略"""
        result = self._execute_query('''
            INSERT INTO strategies (name, symbol, condition_type, target_price, action)
            VALUES (?, ?, ?, ?, ?)
        ''', [name, symbol, condition_type, target_price, action])
        
        return result['result'][0]['meta']['last_row_id']
    
    def get_active_strategies(self) -> List[Dict]:
        """获取所有活跃策略"""
        result = self._execute_query('''
            SELECT * FROM strategies 
            WHERE status = 'active' 
            ORDER BY created_at DESC
        ''')
        
        return result['result'][0]['results']
    
    def trigger_strategy(self, strategy_id: int) -> None:
        """标记策略为已触发"""
        self._execute_query('''
            UPDATE strategies 
            SET status = 'triggered', triggered_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', [strategy_id])
    
    def get_strategies_summary(self) -> Dict:
        """获取策略统计摘要"""
        result = self._execute_query('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                COUNT(CASE WHEN status = 'triggered' THEN 1 END) as triggered
            FROM strategies
        ''')
        
        row = result['result'][0]['results'][0]
        return {
            'total': row['total'],
            'active': row['active'], 
            'triggered': row['triggered']
        }
    
    def save_price(self, price_data: Dict) -> None:
        """保存价格数据"""
        self._execute_query('''
            INSERT INTO price_data (symbol, price, currency, timestamp)
            VALUES (?, ?, ?, ?)
        ''', [
            price_data['symbol'],
            price_data['price'],
            price_data.get('currency', 'USD'),
            price_data.get('timestamp', None)
        ])
    
    def add_notification(self, strategy_id: int, message: str) -> None:
        """添加通知记录"""
        self._execute_query('''
            INSERT INTO notifications (strategy_id, message)
            VALUES (?, ?)
        ''', [strategy_id, message])
    
    def get_recent_notifications(self, limit: int = 20) -> List[Dict]:
        """获取最近的通知记录"""
        result = self._execute_query('''
            SELECT n.message, n.sent_at, s.name as strategy_name
            FROM notifications n
            LEFT JOIN strategies s ON n.strategy_id = s.id
            ORDER BY n.sent_at DESC
            LIMIT ?
        ''', [limit])
        
        return result['result'][0]['results']


def create_database_adapter(config: Dict) -> DatabaseAdapter:
    """数据库适配器工厂方法"""
    adapter_type = config.get('database', {}).get('type', 'sqlite')
    
    if adapter_type == 'sqlite':
        db_path = config.get('database', {}).get('path', config.get('db_path', 'stock_monitor.db'))
        return SQLiteAdapter(db_path)
    
    elif adapter_type == 'cloudflare_d1':
        db_config = config.get('database', {})
        return CloudflareD1Adapter(
            database_id=db_config['database_id'],
            account_id=db_config['account_id'], 
            api_token=db_config['api_token']
        )
    
    else:
        raise ValueError(f"不支持的数据库类型: {adapter_type}")