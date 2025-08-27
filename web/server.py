import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime
from strategy.manager import StrategyManager


class WebServer:
    def __init__(self, config):
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        self.config = config
        self.strategy_manager = StrategyManager(config.get('db_path', 'stock_monitor.db'))
        
        # 注册路由
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            """主页 - 显示策略和通知概览"""
            try:
                # 获取策略统计
                status = self.strategy_manager.get_strategy_status()
                
                # 获取活跃策略及其当前价格
                strategies = self.strategy_manager.get_strategies_with_current_prices()
                
                # 获取最近通知
                notifications = self.get_recent_notifications()
                
                # 统计监控的股票数量
                symbols_count = len(status['by_symbol'])
                
                stats = {
                    'total': status['summary']['total'],
                    'active': status['summary']['active'],
                    'triggered': status['summary']['triggered'],
                    'symbols': symbols_count
                }
                
                return render_template('index.html')
            
            except Exception as e:
                return f"加载数据出错: {e}", 500
        
        @self.app.route('/api/strategies')
        def api_strategies():
            """API - 获取所有策略"""
            try:
                strategies = self.strategy_manager.get_strategies_with_current_prices()
                return jsonify(strategies)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/notifications')
        def api_notifications():
            """API - 获取通知历史"""
            try:
                notifications = self.get_recent_notifications(limit=50)
                return jsonify(notifications)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stats')
        def api_stats():
            """API - 获取统计信息"""
            try:
                status = self.strategy_manager.get_strategy_status()
                symbols_count = len(status['by_symbol'])
                
                stats = {
                    'total': status['summary']['total'],
                    'active': status['summary']['active'],
                    'triggered': status['summary']['triggered'],
                    'symbols': symbols_count,
                    'last_updated': datetime.now().isoformat()
                }
                
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trigger-check')
        def api_trigger_check():
            """API - 手动触发检查"""
            try:
                triggered = self.strategy_manager.check_strategy_triggers()
                
                return jsonify({
                    'success': True,
                    'triggered_count': len(triggered),
                    'triggered_strategies': [t['strategy']['name'] for t in triggered],
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def get_recent_notifications(self, limit=20):
        """获取最近的通知记录"""
        try:
            with sqlite3.connect(self.config.get('db_path', 'stock_monitor.db')) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT n.message, n.sent_at, s.name as strategy_name
                    FROM notifications n
                    LEFT JOIN strategies s ON n.strategy_id = s.id
                    ORDER BY n.sent_at DESC
                    LIMIT ?
                ''', (limit,))
                
                notifications = []
                for row in cursor.fetchall():
                    # 简化消息显示
                    message = row[0]
                    if len(message) > 100:
                        message = message[:100] + "..."
                    
                    notifications.append({
                        'message': message,
                        'sent_at': row[1],
                        'strategy_name': row[2]
                    })
                
                return notifications
        
        except Exception as e:
            print(f"获取通知记录失败: {e}")
            return []
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """启动Web服务器"""
        print(f"🌐 股市监控Web界面启动中...")
        print(f"📱 访问地址: http://{host}:{port}")
        print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
        
        self.app.run(host=host, port=port, debug=debug)


def create_web_server(config):
    """创建Web服务器实例"""
    return WebServer(config)


if __name__ == "__main__":
    # 测试Web服务器
    from monitor.engine import create_default_config
    
    print("=== 股市监控Web服务器测试 ===")
    
    # 使用默认配置
    config = create_default_config()
    
    # 创建Web服务器
    server = create_web_server(config)
    
    print("\n🚀 启动Web服务器...")
    print("访问 http://127.0.0.1:5000 查看监控面板")
    
    try:
        server.run(debug=True)
    except KeyboardInterrupt:
        print("\n🛑 Web服务器已停止")