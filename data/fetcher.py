import requests
from datetime import datetime
from typing import Dict, Optional
import time


class DataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_stock_price(self, symbol: str) -> Optional[Dict]:
        """
        获取股票价格 - 首先尝试Yahoo Finance API，失败则用演示数据
        港股: 0700.HK (腾讯)  
        美股: AAPL
        """
        # 首先尝试Yahoo Finance直接API
        try:
            # 使用Yahoo Finance查询API
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                
                # 获取最新价格
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    current_price = float(result['meta']['regularMarketPrice'])
                    currency = result['meta'].get('currency', 'USD')
                    stock_name = result['meta'].get('longName', symbol)
                    
                    return {
                        'symbol': symbol,
                        'price': current_price,
                        'currency': currency,
                        'name': stock_name,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
        except Exception as e:
            print(f"Yahoo Finance API失败: {e}")
        
        # 如果Yahoo Finance失败，尝试yfinance
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                
                try:
                    info = ticker.info
                    stock_name = info.get('longName', symbol)
                    currency = info.get('currency', 'USD')
                except:
                    stock_name = symbol
                    currency = 'HKD' if symbol.endswith('.HK') else 'USD'
                
                return {
                    'symbol': symbol,
                    'price': current_price,
                    'currency': currency,
                    'name': stock_name,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            print(f"yfinance也失败: {e}")
        
        # 所有方法都失败，使用演示数据
        print(f"获取股票 {symbol} 真实数据失败，使用演示数据")
        return self._get_demo_price(symbol)
    
    def _get_demo_price(self, symbol: str) -> Optional[Dict]:
        """演示数据回退方案"""
        try:
            if symbol.endswith('.HK'):
                # 港股演示数据
                demo_prices = {'0700.HK': 320.50, '0941.HK': 45.20, '2318.HK': 52.80}
                price = demo_prices.get(symbol, 100.0)
                name_map = {'0700.HK': '腾讯控股', '0941.HK': '中国移动', '2318.HK': '中国平安'}
                
                return {
                    'symbol': symbol,
                    'price': price,
                    'currency': 'HKD',
                    'name': name_map.get(symbol, symbol),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' (演示数据)'
                }
            else:
                # 美股演示数据  
                demo_prices = {'AAPL': 175.84, 'MSFT': 428.39, 'GOOGL': 164.72, 'TSLA': 248.50}
                price = demo_prices.get(symbol, 150.0)
                name_map = {'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corp', 'GOOGL': 'Alphabet Inc', 'TSLA': 'Tesla Inc'}
                
                return {
                    'symbol': symbol,
                    'price': price,
                    'currency': 'USD',
                    'name': name_map.get(symbol, symbol),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' (演示数据)'
                }
        except Exception as e:
            print(f"获取演示数据失败: {e}")
            return None
    
    def get_btc_price(self) -> Optional[Dict]:
        """获取BTC价格 - 使用CoinGecko免费API"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            price = float(data['bitcoin']['usd'])
            
            return {
                'symbol': 'BTC-USD',
                'price': price,
                'currency': 'USD',
                'name': 'Bitcoin',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"获取BTC数据失败，使用演示数据: {e}")
            # 返回演示数据
            return {
                'symbol': 'BTC-USD',
                'price': 64250.0,
                'currency': 'USD',
                'name': 'Bitcoin (Demo)',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' (演示数据)'
            }
    
    def get_price(self, symbol: str) -> Optional[Dict]:
        """统一的价格获取接口"""
        if symbol.upper().startswith('BTC'):
            return self.get_btc_price()
        else:
            return self.get_stock_price(symbol)


if __name__ == "__main__":
    # 测试代码
    fetcher = DataFetcher()
    
    print("=== 股市监控数据获取模块测试 ===")
    
    # 测试美股 (苹果)
    print("\n1. 测试美股 - AAPL:")
    aapl_data = fetcher.get_price("AAPL")
    if aapl_data:
        print(f"   {aapl_data['name']}: ${aapl_data['price']:.2f}")
    
    # 测试港股 (腾讯)
    print("\n2. 测试港股 - 0700.HK:")
    tencent_data = fetcher.get_price("0700.HK")
    if tencent_data:
        print(f"   {tencent_data['name']}: {tencent_data['currency']} {tencent_data['price']:.2f}")
    
    # 测试BTC
    print("\n3. 测试比特币 - BTC:")
    btc_data = fetcher.get_price("BTC")
    if btc_data:
        print(f"   {btc_data['name']}: ${btc_data['price']:.2f}")
    
    print("\n✅ 数据获取模块测试完成！")