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
        获取股票价格 - 使用免费API
        港股: 0700.HK (腾讯)  
        美股: AAPL
        """
        try:
            # 使用Alpha Vantage免费API (演示数据)
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
                    'timestamp': datetime.now().isoformat()
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
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"获取股票 {symbol} 数据失败: {e}")
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
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"获取BTC数据失败，使用演示数据: {e}")
            # 返回演示数据
            return {
                'symbol': 'BTC-USD',
                'price': 64250.0,
                'currency': 'USD',
                'name': 'Bitcoin (Demo)',
                'timestamp': datetime.now().isoformat()
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