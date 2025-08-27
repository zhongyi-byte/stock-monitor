import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime


class EmailService:
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587,
                 email: str = "", password: str = ""):
        """
        邮件服务初始化
        
        Args:
            smtp_server: SMTP服务器地址 (Gmail: smtp.gmail.com, QQ: smtp.qq.com)  
            smtp_port: SMTP端口 (通常为587)
            email: 发送者邮箱
            password: 邮箱密码或应用专用密码
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.is_configured = bool(email and password)
    
    def configure(self, email: str, password: str, smtp_server: str = "smtp.gmail.com"):
        """配置邮件账户"""
        self.email = email
        self.password = password
        self.smtp_server = smtp_server
        self.is_configured = True
        print(f"✅ 邮件服务已配置: {email}")
    
    def send_notification(self, to_email: str, subject: str, message: str) -> bool:
        """
        发送邮件通知
        
        Args:
            to_email: 接收者邮箱
            subject: 邮件主题
            message: 邮件内容
            
        Returns:
            发送是否成功
        """
        if not self.is_configured:
            print("❌ 邮件服务未配置，无法发送邮件")
            return False
        
        try:
            # 创建邮件内容
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加邮件正文
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # 创建安全连接并发送邮件
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                text = msg.as_string()
                server.sendmail(self.email, to_email, text)
            
            print(f"✅ 邮件发送成功: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False
    
    def send_trigger_notifications(self, to_email: str, triggered_strategies: List[Dict]) -> int:
        """
        批量发送策略触发通知
        
        Args:
            to_email: 接收者邮箱
            triggered_strategies: 触发的策略列表
            
        Returns:
            成功发送的邮件数量
        """
        if not triggered_strategies:
            return 0
        
        success_count = 0
        
        for trigger_info in triggered_strategies:
            strategy = trigger_info['strategy']
            
            # 生成邮件主题
            subject = f"🚨 股市监控提醒 - {strategy['name']}"
            
            # 生成邮件内容
            message = self._format_email_message(trigger_info)
            
            # 发送邮件
            if self.send_notification(to_email, subject, message):
                success_count += 1
        
        return success_count
    
    def _format_email_message(self, trigger_info: Dict) -> str:
        """格式化邮件消息"""
        strategy = trigger_info['strategy']
        current_price = trigger_info['current_price']
        currency = trigger_info['currency']
        stock_name = trigger_info['stock_name']
        
        condition_text = "低于" if strategy['condition_type'] == 'below' else "高于"
        action_text = {
            'buy': '🟢 买入提醒',
            'sell': '🔴 卖出提醒', 
            'notify': '🔔 价格提醒'
        }.get(strategy['action'], '🔔 提醒')
        
        message = f"""
{action_text}

策略名称: {strategy['name']}
股票信息: {stock_name} ({strategy['symbol']})
当前价格: {currency} {current_price:.2f}
触发条件: 价格{condition_text} {currency} {strategy['target_price']:.2f}
触发时间: {trigger_info['trigger_time']}

建议行动: {strategy['action']}

⚠️  请注意风险控制，理性投资！

---
股市监控系统自动发送
发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        return message
    
    def test_email_connection(self) -> bool:
        """测试邮件连接"""
        if not self.is_configured:
            print("❌ 邮件服务未配置")
            return False
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
            
            print("✅ 邮件服务连接测试成功")
            return True
            
        except Exception as e:
            print(f"❌ 邮件服务连接测试失败: {e}")
            return False
    
    def send_test_email(self, to_email: str) -> bool:
        """发送测试邮件"""
        subject = "📧 股市监控系统 - 测试邮件"
        message = f"""
这是一封测试邮件，用于验证股市监控系统的邮件通知功能。

如果您收到这封邮件，说明邮件服务配置成功！

系统信息:
- 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 发送者: {self.email}
- SMTP服务器: {self.smtp_server}

接下来您可以开始设置股票监控策略了。

---
股市监控系统
        """.strip()
        
        return self.send_notification(to_email, subject, message)


if __name__ == "__main__":
    # 测试邮件服务模块
    print("=== 邮件通知服务测试 ===")
    
    # 创建邮件服务实例（演示模式）
    email_service = EmailService()
    
    # 测试未配置状态
    print("\n1. 测试未配置状态:")
    print(f"   邮件服务配置状态: {'已配置' if email_service.is_configured else '未配置'}")
    
    # 模拟配置邮件服务
    print("\n2. 模拟配置邮件服务:")
    email_service.configure(
        email="your-email@gmail.com",
        password="your-app-password",
        smtp_server="smtp.gmail.com"
    )
    
    # 测试触发通知格式化
    print("\n3. 测试触发通知消息格式:")
    
    # 模拟触发数据
    mock_trigger_info = {
        'strategy': {
            'id': 1,
            'name': '苹果低价买入机会',
            'symbol': 'AAPL',
            'condition_type': 'below',
            'target_price': 170.0,
            'action': 'buy'
        },
        'current_price': 168.50,
        'currency': 'USD',
        'stock_name': 'Apple Inc.',
        'trigger_time': datetime.now().isoformat()
    }
    
    formatted_message = email_service._format_email_message(mock_trigger_info)
    print("   格式化后的邮件内容:")
    print("   " + "\n   ".join(formatted_message.split("\n")))
    
    # 测试批量通知（演示模式）
    print("\n4. 测试批量通知功能:")
    mock_triggers = [mock_trigger_info]
    
    print("   注意: 实际发送需要真实的邮箱配置")
    print(f"   模拟发送 {len(mock_triggers)} 个通知到: test@example.com")
    
    # 不实际发送，只是演示
    print("   (演示模式，不会真实发送邮件)")
    
    print("\n5. 邮件服务配置说明:")
    print("   Gmail用户:")
    print("   1. 开启两步验证")  
    print("   2. 生成应用专用密码")
    print("   3. 使用应用专用密码而非普通密码")
    print("   4. SMTP服务器: smtp.gmail.com")
    
    print("\n   QQ邮箱用户:")
    print("   1. 开启SMTP服务")
    print("   2. 获取授权码")
    print("   3. 使用授权码而非QQ密码")
    print("   4. SMTP服务器: smtp.qq.com")
    
    print("\n✅ 邮件通知服务测试完成！")