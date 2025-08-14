import requests
from bs4 import BeautifulSoup
import time
import random
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class AppStoreCrawler:
    def __init__(self):
        # 预定义一些常用的User-Agent
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.5; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
        ]
        
        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 加载简化的国家代码映射表（只包含常用国家）
        self.country_codes = self._load_country_codes()
        
    def _load_country_codes(self):
        """加载简化的国家代码映射表"""
        return {
            "US": "United States",
            "CN": "China",
            "JP": "Japan",
            "KR": "Korea",
            "GB": "United Kingdom",
            "DE": "Germany",
            "FR": "France",
            "IT": "Italy",
            "ES": "Spain",
            "IN": "India",
            "CA": "Canada",
            "AU": "Australia",
            "BR": "Brazil",
            "RU": "Russia",
            "MX": "Mexico",
            "SE": "Sweden",
            "NL": "Netherlands",
            "CH": "Switzerland",
            "SG": "Singapore",
            "HK": "Hong Kong",
            "TW": "Taiwan",
            "TH": "Thailand",
            "MY": "Malaysia",
            "ID": "Indonesia",
            "VN": "Vietnam",
            "PH": "Philippines",
            "TR": "Turkey",
            "SA": "Saudi Arabia",
            "AE": "United Arab Emirates",
            "IL": "Israel",
            "ZA": "South Africa",
        }
    
    def _get_random_delay(self):
        """获取随机延迟时间，防止请求过于频繁"""
        return random.uniform(2, 5)
    
    def _get_random_user_agent(self):
        """获取随机的User-Agent"""
        return random.choice(self.user_agents)
    
    def get_google_play_app_info(self, app_id, countries=None):
        """获取Google Play应用在不同国家的上线信息"""
        if countries is None:
            countries = list(self.country_codes.keys())
            
        results = []
        
        for country in countries:
            time.sleep(self._get_random_delay())  # 添加随机延迟
            
            # 每次请求使用不同的User-Agent
            self.headers['User-Agent'] = self._get_random_user_agent()
            
            try:
                url = f"https://play.google.com/store/apps/details?id={app_id}&gl={country}"
                response = self.session.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 使用新的选择器获取应用名称
                    title_element = soup.find('span', class_='AfwdI')
                    
                    if title_element:
                        app_name = title_element.text.strip()
                        
                        # 使用新的选择器获取应用简介
                        description_element = soup.find('div', class_='bARER')
                        if description_element:
                            # 截取简介的前50个字符作为预览
                            description_preview = description_element.text.strip()[:50] + "..." if len(description_element.text.strip()) > 50 else description_element.text.strip()
                            
                            results.append({
                                'country_code': country,
                                'country_name': self.country_codes.get(country, country),
                                'app_name': app_name,
                                'description_preview': description_preview,
                                'url': url,
                                'available': True
                            })
                        else:
                            results.append({
                                'country_code': country,
                                'country_name': self.country_codes.get(country, country),
                                'app_name': app_name,
                                'description_preview': '无法获取简介',
                                'url': url,
                                'available': True
                            })
                    else:
                        # 检查是否是"App not found"页面
                        not_found_element = soup.find('div', class_='bARER')
                        if not_found_element and "找不到" in not_found_element.text:
                            results.append({
                                'country_code': country,
                                'country_name': self.country_codes.get(country, country),
                                'app_name': None,
                                'description_preview': None,
                                'url': url,
                                'available': False,
                                'error': '应用在该国不可用'
                            })
                        else:
                            # 页面结构可能已更改，需要进一步分析
                            results.append({
                                'country_code': country,
                                'country_name': self.country_codes.get(country, country),
                                'app_name': None,
                                'description_preview': None,
                                'url': url,
                                'available': False,
                                'error': '无法解析页面结构'
                            })
                else:
                    print(f"请求失败，状态码: {response.status_code}, 国家: {country}")
                    results.append({
                        'country_code': country,
                        'country_name': self.country_codes.get(country, country),
                        'app_name': None,
                        'description_preview': None,
                        'url': url,
                        'available': False,
                        'error': f"Status code: {response.status_code}"
                    })
                    
            except Exception as e:
                print(f"发生错误: {str(e)}, 国家: {country}")
                results.append({
                    'country_code': country,
                    'country_name': self.country_codes.get(country, country),
                    'app_name': None,
                    'description_preview': None,
                    'url': url,
                    'available': False,
                    'error': str(e)
                })
        
        return results
    
    def export_to_csv(self, results, filename):
        """将结果导出为CSV文件"""
        df = pd.DataFrame(results)
        df.to_csv(filename, index=False)
        print(f"结果已导出到 {filename}")

# 使用示例
if __name__ == "__main__":
    crawler = AppStoreCrawler()
    
    # 示例：获取Google Play上微信的信息
    google_play_results = crawler.get_google_play_app_info(
        app_id="com.tencent.mm",
        countries=["US", "CN", "JP", "KR", "GB", "DE", "FR"]
    )
    
    # 打印结果
    print("\nGoogle Play 结果:")
    for result in google_play_results:
        status = "可用" if result['available'] else "不可用"
        app_info = f"{result['app_name']} - {result['description_preview']}" if result['available'] else "N/A"
        print(f"{result['country_name']}: {status} - {app_info}")
    
    # 导出结果到CSV文件
    crawler.export_to_csv(google_play_results, "google_play_results.csv")    