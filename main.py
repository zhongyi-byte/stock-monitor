#!/usr/bin/env python3
"""
股市监控系统 - 主程序
支持港股、美股、比特币价格监控，当价格触发设定条件时通过邮件通知
"""

import argparse
import json
from pathlib import Path
from typing import Dict

from strategy.manager import StrategyManager
from monitor.engine import MonitorEngine
from notification.email_service import EmailService
from config.manager import ConfigManager, create_default_config


def load_config(config_path: str = "config.json") -> ConfigManager:
    """加载配置 - 使用新的配置管理器"""
    config_manager = ConfigManager(config_path)
    
    # 如果配置文件不存在，保存默认配置
    config_file = Path(config_path)
    if not config_file.exists():
        config_manager.save(config_path)
        print(f"✅ 已创建默认配置文件: {config_path}")
        print("⚠️  请编辑配置文件设置邮件服务后重新运行")
    
    return config_manager


def setup_email_config():
    """交互式设置邮件配置"""
    print("\n📧 邮件服务配置向导")
    print("支持的邮件服务商:")
    print("1. Gmail (smtp.gmail.com)")
    print("2. QQ邮箱 (smtp.qq.com)")
    print("3. 163邮箱 (smtp.163.com)")
    print("4. 自定义")
    
    choice = input("\n请选择邮件服务商 (1-4): ").strip()
    
    smtp_servers = {
        '1': 'smtp.gmail.com',
        '2': 'smtp.qq.com', 
        '3': 'smtp.163.com',
        '4': None
    }
    
    smtp_server = smtp_servers.get(choice)
    if smtp_server is None:
        smtp_server = input("请输入SMTP服务器地址: ").strip()
    
    sender_email = input("发送者邮箱: ").strip()
    password = input("邮箱密码/授权码: ").strip()
    recipient_email = input("接收通知的邮箱: ").strip()
    
    # 测试邮件连接
    print("\n🔍 测试邮件连接...")
    email_service = EmailService()
    email_service.configure(sender_email, password, smtp_server)
    
    if email_service.test_email_connection():
        # 发送测试邮件
        if input("是否发送测试邮件? (y/N): ").lower() == 'y':
            email_service.send_test_email(recipient_email)
        
        return {
            'enabled': True,
            'sender_email': sender_email,
            'password': password,
            'recipient_email': recipient_email,
            'smtp_server': smtp_server
        }
    else:
        print("❌ 邮件配置失败，请检查设置")
        return {'enabled': False}


def add_strategy_interactive(manager: StrategyManager):
    """交互式添加监控策略"""
    print("\n📈 添加监控策略")
    
    name = input("策略名称: ").strip()
    
    print("\n支持的股票类型:")
    print("- 美股: AAPL, MSFT, GOOGL, TSLA 等")
    print("- 港股: 0700.HK (腾讯), 0941.HK (中国移动) 等")
    print("- 比特币: BTC")
    
    symbol = input("股票/币种代码: ").strip().upper()
    
    print("\n触发条件:")
    print("1. below - 价格低于目标值时触发")
    print("2. above - 价格高于目标值时触发")
    
    condition_choice = input("选择条件 (1-2): ").strip()
    condition_type = 'below' if condition_choice == '1' else 'above'
    
    target_price = float(input("目标价格: ").strip())
    
    print("\n触发动作:")
    print("1. notify - 仅通知")
    print("2. buy - 买入提醒")
    print("3. sell - 卖出提醒")
    
    action_choice = input("选择动作 (1-3): ").strip()
    actions = {'1': 'notify', '2': 'buy', '3': 'sell'}
    action = actions.get(action_choice, 'notify')
    
    try:
        strategy_id = manager.create_strategy(name, symbol, condition_type, target_price, action)
        print(f"✅ 策略创建成功! ID: {strategy_id}")
        
        # 显示策略详情
        condition_text = "低于" if condition_type == 'below' else "高于"
        print(f"📋 策略详情: {name}")
        print(f"    股票: {symbol}")
        print(f"    条件: 价格{condition_text} {target_price} 时{action}")
        
    except Exception as e:
        print(f"❌ 策略创建失败: {e}")


def list_strategies(manager: StrategyManager):
    """列出所有策略"""
    print("\n📊 当前监控策略")
    
    strategies = manager.get_all_strategies()
    status = manager.get_strategy_status()
    
    print(f"总策略: {status['summary']['total']}, 活跃: {status['summary']['active']}, 已触发: {status['summary']['triggered']}")
    
    if not strategies:
        print("暂无活跃策略")
        return
    
    print("\n活跃策略列表:")
    for i, s in enumerate(strategies, 1):
        condition_text = "低于" if s['condition_type'] == 'below' else "高于"
        print(f"{i}. {s['name']}")
        print(f"   股票: {s['symbol']} | 触发条件: 价格{condition_text} {s['target_price']} | 动作: {s['action']}")
        print(f"   创建时间: {s['created_at']}")


def main():
    parser = argparse.ArgumentParser(description='股市监控系统')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    parser.add_argument('--setup', action='store_true', help='设置邮件配置')
    parser.add_argument('--add-strategy', action='store_true', help='添加监控策略')
    parser.add_argument('--list-strategies', action='store_true', help='列出所有策略')
    parser.add_argument('--run-once', action='store_true', help='手动执行一次检查')
    parser.add_argument('--start', action='store_true', help='启动监控系统')
    parser.add_argument('--web', action='store_true', help='启动Web管理界面')
    parser.add_argument('--port', type=int, default=5000, help='Web服务器端口（默认5000）')
    
    args = parser.parse_args()
    
    print("🚀 股市监控系统")
    print("支持港股、美股、比特币监控")
    
    # 加载配置
    config_manager = load_config(args.config)
    config = config_manager.get_all()
    
    # 邮件配置设置
    if args.setup:
        email_config = setup_email_config()
        # 更新配置管理器
        for key, value in email_config.items():
            config_manager.set(f'email.{key}', value)
        
        # 保存配置
        config_manager.save(args.config)
        print("✅ 配置已保存")
        return
    
    # 创建管理器 - 使用新的配置系统
    manager = StrategyManager(config=config)
    
    # 添加策略
    if args.add_strategy:
        add_strategy_interactive(manager)
        return
    
    # 列出策略
    if args.list_strategies:
        list_strategies(manager)
        return
    
    # 创建监控引擎
    engine = MonitorEngine(config)
    
    # 手动执行检查
    if args.run_once:
        engine.run_once()
        return
    
    # 启动监控系统
    if args.start:
        engine.start_monitoring()
        return
    
    # 启动Web管理界面
    if args.web:
        try:
            from web.server import create_web_server
            web_server = create_web_server(config)
            web_server.run(host='0.0.0.0', port=args.port, debug=False)
        except ImportError:
            print("❌ 缺少Flask依赖，请先安装:")
            print("pip install flask==3.0.0")
        except Exception as e:
            print(f"❌ Web服务器启动失败: {e}")
        return
    
    # 默认显示帮助信息
    print("\n使用方法:")
    print("  python main.py --setup              # 设置邮件配置")
    print("  python main.py --add-strategy       # 添加监控策略")  
    print("  python main.py --list-strategies    # 查看所有策略")
    print("  python main.py --run-once           # 手动执行一次检查")
    print("  python main.py --start              # 启动监控系统")
    print("  python main.py --web                # 启动Web管理界面")
    print("  python main.py --web --port 8080    # 指定Web端口")
    print("\n更多帮助: python main.py --help")


if __name__ == "__main__":
    main()