"""
配置管理模块 - 支持本地配置文件 + 云端环境变量
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """配置管理器 - 统一管理本地和云端配置"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self._config = {}
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置 - 优先级: 环境变量 > 配置文件 > 默认值"""
        # 1. 加载默认配置
        self._config = self._get_default_config()
        
        # 2. 加载配置文件（如果存在）
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                self._merge_config(file_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        
        # 3. 覆盖环境变量配置
        self._load_from_env()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "database": {
                "type": "sqlite",  # 'sqlite' 或 'cloudflare_d1'
                "path": "stock_monitor.db"
            },
            "email": {
                "enabled": False,
                "sender_email": "",
                "password": "", 
                "recipient_email": "",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587
            },
            "monitoring": {
                "check_interval": 300,  # 5分钟
                "daily_time": "09:30",
                "timezone": "Asia/Shanghai"
            },
            "web": {
                "host": "127.0.0.1",
                "port": 5000,
                "debug": False
            },
            "deployment": {
                "type": "local",  # 'local', 'cloudflare', 'docker'
                "environment": "development"  # 'development', 'production'
            }
        }
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """深度合并配置"""
        def merge_dict(base: Dict, update: Dict) -> Dict:
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value
            return base
        
        merge_dict(self._config, new_config)
    
    def _load_from_env(self) -> None:
        """从环境变量加载配置"""
        # 数据库配置
        if os.getenv('DB_TYPE'):
            self._config['database']['type'] = os.getenv('DB_TYPE')
        if os.getenv('DB_PATH'):
            self._config['database']['path'] = os.getenv('DB_PATH')
        
        # Cloudflare D1 配置
        if os.getenv('CF_DATABASE_ID'):
            self._config['database']['database_id'] = os.getenv('CF_DATABASE_ID')
        if os.getenv('CF_ACCOUNT_ID'):
            self._config['database']['account_id'] = os.getenv('CF_ACCOUNT_ID')
        if os.getenv('CF_API_TOKEN'):
            self._config['database']['api_token'] = os.getenv('CF_API_TOKEN')
        
        # 邮件配置
        if os.getenv('EMAIL_ENABLED'):
            self._config['email']['enabled'] = os.getenv('EMAIL_ENABLED').lower() == 'true'
        if os.getenv('SENDER_EMAIL'):
            self._config['email']['sender_email'] = os.getenv('SENDER_EMAIL')
        if os.getenv('EMAIL_PASSWORD'):
            self._config['email']['password'] = os.getenv('EMAIL_PASSWORD')
        if os.getenv('RECIPIENT_EMAIL'):
            self._config['email']['recipient_email'] = os.getenv('RECIPIENT_EMAIL')
        if os.getenv('SMTP_SERVER'):
            self._config['email']['smtp_server'] = os.getenv('SMTP_SERVER')
        if os.getenv('SMTP_PORT'):
            self._config['email']['smtp_port'] = int(os.getenv('SMTP_PORT'))
        
        # Web配置
        if os.getenv('WEB_HOST'):
            self._config['web']['host'] = os.getenv('WEB_HOST')
        if os.getenv('WEB_PORT'):
            self._config['web']['port'] = int(os.getenv('WEB_PORT'))
        if os.getenv('WEB_DEBUG'):
            self._config['web']['debug'] = os.getenv('WEB_DEBUG').lower() == 'true'
        
        # 部署配置
        if os.getenv('DEPLOYMENT_TYPE'):
            self._config['deployment']['type'] = os.getenv('DEPLOYMENT_TYPE')
        if os.getenv('ENVIRONMENT'):
            self._config['deployment']['environment'] = os.getenv('ENVIRONMENT')
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值 - 支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, config_path: Optional[str] = None) -> None:
        """保存配置到文件"""
        if config_path is None:
            config_path = self.config_path
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def is_local_deployment(self) -> bool:
        """判断是否为本地部署"""
        return self.get('deployment.type') == 'local'
    
    def is_cloudflare_deployment(self) -> bool:
        """判断是否为Cloudflare部署"""
        return self.get('deployment.type') == 'cloudflare'
    
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.get('deployment.environment') == 'production'


def create_config_manager(config_path: str = "config.json") -> ConfigManager:
    """创建配置管理器实例"""
    return ConfigManager(config_path)


def create_default_config() -> Dict[str, Any]:
    """创建默认配置 - 兼容性函数"""
    manager = ConfigManager()
    return manager.get_all()


if __name__ == "__main__":
    # 测试配置管理
    print("=== 配置管理模块测试 ===")
    
    # 创建配置管理器
    config = ConfigManager("test_config.json")
    
    print("1. 默认配置:")
    print(f"   数据库类型: {config.get('database.type')}")
    print(f"   邮件启用: {config.get('email.enabled')}")
    print(f"   Web端口: {config.get('web.port')}")
    
    print("\n2. 设置新配置:")
    config.set('database.type', 'cloudflare_d1')
    config.set('email.enabled', True)
    config.set('web.port', 8080)
    
    print(f"   数据库类型: {config.get('database.type')}")
    print(f"   邮件启用: {config.get('email.enabled')}")
    print(f"   Web端口: {config.get('web.port')}")
    
    print("\n3. 环境变量测试:")
    os.environ['DB_TYPE'] = 'sqlite'
    os.environ['WEB_PORT'] = '3000'
    
    # 重新加载配置
    config.load_config()
    print(f"   数据库类型(环境变量): {config.get('database.type')}")
    print(f"   Web端口(环境变量): {config.get('web.port')}")
    
    print("\n4. 部署类型判断:")
    print(f"   是否本地部署: {config.is_local_deployment()}")
    print(f"   是否Cloudflare部署: {config.is_cloudflare_deployment()}")
    print(f"   是否生产环境: {config.is_production()}")
    
    print("\n✅ 配置管理模块测试完成！")
    
    # 清理
    Path("test_config.json").unlink(missing_ok=True)
    del os.environ['DB_TYPE']
    del os.environ['WEB_PORT']