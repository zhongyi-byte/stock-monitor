import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional
from data.storage import Database
from data.fetcher import DataFetcher
from data.database_adapter import create_database_adapter


class StrategyManager:
    def __init__(self, config: Dict = None, db_path: str = "stock_monitor.db"):
        """
        策略管理器
        
        Args:
            config: 配置字典，如果提供则使用适配器模式
            db_path: SQLite数据库路径（向后兼容）
        """
        if config:
            # 使用配置创建数据库适配器
            adapter = create_database_adapter(config)
            self.db = Database(adapter=adapter)
        else:
            # 向后兼容，使用SQLite
            self.db = Database(db_path=db_path)
            
        self.fetcher = DataFetcher()
    
    def create_strategy(self, name: str, symbol: str, condition_type: str, 
                       target_price: float, action: str = 'notify') -> int:
        """
        创建监控策略
        
        Args:
            name: 策略名称
            symbol: 股票代码 (如 AAPL, 0700.HK, BTC)
            condition_type: 条件类型 ('below' 或 'above')
            target_price: 目标价格
            action: 触发动作 ('buy', 'sell', 'notify')
        
        Returns:
            策略ID
        """
        # 验证参数
        if condition_type not in ['below', 'above']:
            raise ValueError("condition_type 必须是 'below' 或 'above'")
        
        if action not in ['buy', 'sell', 'notify']:
            raise ValueError("action 必须是 'buy', 'sell' 或 'notify'")
        
        if target_price <= 0:
            raise ValueError("target_price 必须大于0")
        
        return self.db.add_strategy(name, symbol, condition_type, target_price, action)
    
    def get_all_strategies(self) -> List[Dict]:
        """获取所有活跃策略"""
        return self.db.get_active_strategies()
    
    def get_strategies_with_current_prices(self) -> List[Dict]:
        """获取所有活跃策略及其当前价格"""
        strategies = self.db.get_active_strategies()
        
        for strategy in strategies:
            symbol = strategy['symbol']
            
            # 获取当前价格数据
            current_price_data = self.fetcher.get_price(symbol)
            if current_price_data:
                strategy['current_price'] = current_price_data['price']
                strategy['currency'] = current_price_data.get('currency', 'USD')
                strategy['last_updated'] = current_price_data.get('timestamp', '')
            else:
                strategy['current_price'] = None
                strategy['currency'] = 'USD'
                strategy['last_updated'] = ''
        
        return strategies
    
    def check_strategy_triggers(self) -> List[Dict]:
        """
        检查所有策略是否触发
        
        Returns:
            触发的策略列表
        """
        triggered_strategies = []
        active_strategies = self.db.get_active_strategies()
        
        for strategy in active_strategies:
            symbol = strategy['symbol']
            
            # 获取当前价格
            current_price_data = self.fetcher.get_price(symbol)
            if not current_price_data:
                print(f"无法获取 {symbol} 的价格数据")
                continue
            
            current_price = current_price_data['price']
            target_price = strategy['target_price']
            condition_type = strategy['condition_type']
            
            # 保存价格数据到数据库
            self.db.save_price(current_price_data)
            
            # 检查是否触发条件
            is_triggered = False
            if condition_type == 'below' and current_price <= target_price:
                is_triggered = True
            elif condition_type == 'above' and current_price >= target_price:
                is_triggered = True
            
            if is_triggered:
                # 标记策略为已触发
                self.db.trigger_strategy(strategy['id'])
                
                # 构建触发信息
                trigger_info = {
                    'strategy': strategy,
                    'current_price': current_price,
                    'currency': current_price_data['currency'],
                    'stock_name': current_price_data['name'],
                    'trigger_time': current_price_data['timestamp']
                }
                
                triggered_strategies.append(trigger_info)
                
                print(f"🚨 策略触发: {strategy['name']}")
                print(f"   {trigger_info['stock_name']} 当前价格: {trigger_info['currency']} {current_price}")
                print(f"   触发条件: {condition_type} {target_price}")
        
        return triggered_strategies
    
    def format_trigger_message(self, trigger_info: Dict) -> str:
        """格式化触发消息"""
        strategy = trigger_info['strategy']
        current_price = trigger_info['current_price']
        currency = trigger_info['currency']
        stock_name = trigger_info['stock_name']
        
        condition_text = "低于" if strategy['condition_type'] == 'below' else "高于"
        action_text = {
            'buy': '买入提醒',
            'sell': '卖出提醒', 
            'notify': '价格提醒'
        }.get(strategy['action'], '提醒')
        
        message = f"""
🚨 股市监控提醒 - {action_text}

策略名称: {strategy['name']}
股票信息: {stock_name} ({strategy['symbol']})
当前价格: {currency} {current_price:.2f}
触发条件: 价格{condition_text} {currency} {strategy['target_price']:.2f}
触发时间: {trigger_info['trigger_time']}

请及时关注市场变化！
        """.strip()
        
        return message
    
    def get_strategy_status(self) -> Dict:
        """获取策略状态统计"""
        summary = self.db.get_strategies_summary()
        strategies = self.get_all_strategies()
        
        # 按股票分组
        by_symbol = {}
        for s in strategies:
            symbol = s['symbol']
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(s)
        
        return {
            'summary': summary,
            'by_symbol': by_symbol,
            'total_active': len(strategies)
        }


if __name__ == "__main__":
    # 测试策略管理模块
    print("=== 策略管理模块测试 ===")
    
    # 创建策略管理器
    manager = StrategyManager("test_strategy.db")
    
    # 测试创建策略
    print("\n1. 创建监控策略:")
    try:
        s1 = manager.create_strategy("苹果低价买入机会", "AAPL", "below", 170.0, "buy")
        s2 = manager.create_strategy("腾讯突破新高", "0700.HK", "above", 350.0, "notify")  
        s3 = manager.create_strategy("比特币回调买入", "BTC", "below", 60000.0, "buy")
        print(f"   成功创建3个策略，ID: {s1}, {s2}, {s3}")
    except Exception as e:
        print(f"   创建策略失败: {e}")
    
    # 测试获取所有策略
    print("\n2. 查看所有活跃策略:")
    strategies = manager.get_all_strategies()
    for s in strategies:
        condition_text = "低于" if s['condition_type'] == 'below' else "高于"
        print(f"   {s['name']}: {s['symbol']} 价格{condition_text} {s['target_price']} 时{s['action']}")
    
    # 测试检查策略触发
    print("\n3. 检查策略触发情况:")
    triggered = manager.check_strategy_triggers()
    
    if triggered:
        print(f"   发现 {len(triggered)} 个策略被触发:")
        for t in triggered:
            print(f"   - {t['strategy']['name']}")
            print(f"     {t['stock_name']}: {t['currency']} {t['current_price']}")
    else:
        print("   当前没有策略被触发")
    
    # 测试消息格式化
    if triggered:
        print("\n4. 触发消息示例:")
        message = manager.format_trigger_message(triggered[0])
        print(message)
    
    # 测试策略状态
    print("\n5. 策略状态统计:")
    status = manager.get_strategy_status()
    print(f"   总策略: {status['summary']['total']}")
    print(f"   活跃策略: {status['summary']['active']}")
    print(f"   已触发: {status['summary']['triggered']}")
    print(f"   监控股票数: {len(status['by_symbol'])}")
    
    print("\n✅ 策略管理模块测试完成！")
    
    # 清理测试文件
    from pathlib import Path
    Path("test_strategy.db").unlink(missing_ok=True)