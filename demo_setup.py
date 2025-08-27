#!/usr/bin/env python3
"""
演示数据设置脚本 - 为Web界面创建示例数据
"""

import sys
from strategy.manager import StrategyManager

def setup_demo_data():
    """创建演示策略和通知数据"""
    print("🎯 创建演示数据...")
    
    # 创建策略管理器
    manager = StrategyManager("stock_monitor.db")
    
    # 添加演示策略
    demo_strategies = [
        ("苹果低价买入机会", "AAPL", "below", 170.0, "buy"),
        ("腾讯突破新高", "0700.HK", "above", 350.0, "notify"), 
        ("比特币回调买入", "BTC", "below", 60000.0, "buy"),
        ("微软高价卖出", "MSFT", "above", 450.0, "sell"),
        ("特斯拉价格提醒", "TSLA", "below", 200.0, "notify")
    ]
    
    print(f"添加 {len(demo_strategies)} 个演示策略:")
    
    for name, symbol, condition, price, action in demo_strategies:
        try:
            strategy_id = manager.create_strategy(name, symbol, condition, price, action)
            condition_text = "低于" if condition == "below" else "高于"
            print(f"  ✅ {name}: {symbol} 价格{condition_text} {price} 时{action}")
        except Exception as e:
            print(f"  ❌ 创建策略失败: {e}")
    
    # 手动执行一次检查来生成一些通知数据
    print("\n🔍 执行策略检查...")
    triggered = manager.check_strategy_triggers()
    
    if triggered:
        print(f"触发了 {len(triggered)} 个策略，已生成通知记录")
    else:
        print("当前价格未触发任何策略")
    
    # 显示统计信息
    status = manager.get_strategy_status()
    print(f"\n📊 当前状态:")
    print(f"  总策略: {status['summary']['total']}")
    print(f"  活跃策略: {status['summary']['active']}")
    print(f"  已触发: {status['summary']['triggered']}")
    print(f"  监控股票: {len(status['by_symbol'])}")
    
    print("\n✅ 演示数据设置完成!")
    print("现在可以启动Web界面查看效果:")
    print("  python main.py --web")


if __name__ == "__main__":
    setup_demo_data()