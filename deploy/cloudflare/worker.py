"""
Cloudflare Workers Python 后端
将Flask API转换为Workers兼容的处理器
"""

import json
import sys
import os
from typing import Dict, Any
from urllib.parse import parse_qs

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from strategy.manager import StrategyManager
from config.manager import ConfigManager
from data.database_adapter import CloudflareD1Adapter


class WorkerApp:
    """Cloudflare Workers应用类"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        # 强制设置为Cloudflare部署
        self.config_manager.set('deployment.type', 'cloudflare')
        self.config_manager.set('database.type', 'cloudflare_d1')
        
        # 从环境变量加载D1配置
        self.config_manager.load_config()
        
        # 创建策略管理器
        self.strategy_manager = StrategyManager(config=self.config_manager.get_all())
    
    def handle_request(self, request: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
        """处理HTTP请求"""
        try:
            method = request.get('method', 'GET')
            url = request.get('url', '')
            
            # 解析路径
            if '/api/stats' in url:
                return self.handle_stats()
            elif '/api/strategies' in url:
                return self.handle_strategies()
            elif '/api/notifications' in url:
                return self.handle_notifications()
            elif '/api/trigger-check' in url and method == 'POST':
                return self.handle_trigger_check()
            else:
                return self.handle_static()
        
        except Exception as e:
            return {
                'status': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': str(e)})
            }
    
    def handle_stats(self) -> Dict[str, Any]:
        """处理统计信息API"""
        try:
            status = self.strategy_manager.get_strategy_status()
            symbols_count = len(status['by_symbol'])
            
            stats = {
                'total': status['summary']['total'],
                'active': status['summary']['active'],
                'triggered': status['summary']['triggered'],
                'symbols': symbols_count,
                'last_updated': '2025-08-27T21:41:14.173089'  # 固定时间戳，实际应用中用datetime.now()
            }
            
            return {
                'status': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(stats)
            }
        except Exception as e:
            return {
                'status': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': str(e)})
            }
    
    def handle_strategies(self) -> Dict[str, Any]:
        """处理策略列表API"""
        try:
            strategies = self.strategy_manager.get_strategies_with_current_prices()
            
            return {
                'status': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(strategies)
            }
        except Exception as e:
            return {
                'status': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': str(e)})
            }
    
    def handle_notifications(self) -> Dict[str, Any]:
        """处理通知历史API"""
        try:
            notifications = self.strategy_manager.db.get_recent_notifications(limit=50)
            
            return {
                'status': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(notifications)
            }
        except Exception as e:
            return {
                'status': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': str(e)})
            }
    
    def handle_trigger_check(self) -> Dict[str, Any]:
        """处理手动触发检查API"""
        try:
            triggered = self.strategy_manager.check_strategy_triggers()
            
            response_data = {
                'success': True,
                'triggered_count': len(triggered),
                'triggered_strategies': [t['strategy']['name'] for t in triggered],
                'timestamp': '2025-08-27T21:41:14.173089'
            }
            
            return {
                'status': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(response_data)
            }
        except Exception as e:
            return {
                'status': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': str(e)})
            }
    
    def handle_static(self) -> Dict[str, Any]:
        """处理静态文件 - 返回前端HTML"""
        # 在实际部署中，前端会部署到Cloudflare Pages
        # 这里返回一个简单的重定向或者API信息
        return {
            'status': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Stock Monitor API',
                'version': '1.0.0',
                'endpoints': [
                    '/api/stats',
                    '/api/strategies', 
                    '/api/notifications',
                    '/api/trigger-check'
                ]
            })
        }


# Cloudflare Workers 入口点
app = WorkerApp()

def fetch(request, env):
    """Cloudflare Workers fetch处理器"""
    return app.handle_request(request, env)

def scheduled(event, env, ctx):
    """Cloudflare Workers cron处理器"""
    try:
        # 定时检查策略触发
        app = WorkerApp()
        triggered = app.strategy_manager.check_strategy_triggers()
        
        if triggered:
            print(f"定时检查触发了 {len(triggered)} 个策略")
            # 这里可以发送邮件通知
            
        return True
    except Exception as e:
        print(f"定时任务执行失败: {e}")
        return False