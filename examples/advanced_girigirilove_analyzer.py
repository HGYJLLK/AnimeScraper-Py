#!/usr/bin/env python3
"""
高级 girigirilove 网站分析工具
处理403错误和寻找真实的搜索API
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urljoin, parse_qs, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from web_scraper.utils.logger import logger


class GirigiriloveAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://anime.girigirilove.com"
        
        # 模拟更真实的浏览器环境
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(self.headers)
    
    def analyze_main_page(self):
        """深度分析主页结构"""
        logger.info("=== 深度分析主页结构 ===")
        
        try:
            response = self.session.get(self.base_url, timeout=15)
            logger.info(f"主页状态码: {response.status_code}")
            
            if response.status_code != 200:
                logger.error("主页访问失败")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 分析搜索表单
            forms = soup.find_all('form')
            logger.info(f"找到 {len(forms)} 个表单")
            
            for i, form in enumerate(forms):
                action = form.get('action', '')
                method = form.get('method', 'GET')
                logger.info(f"表单 {i+1}: method={method}, action={action}")
                
                # 分析表单中的输入字段
                inputs = form.find_all(['input', 'select', 'textarea'])
                for inp in inputs:
                    name = inp.get('name', '')
                    inp_type = inp.get('type', inp.name)
                    placeholder = inp.get('placeholder', '')
                    if name or placeholder:
                        logger.info(f"  输入字段: name='{name}', type={inp_type}, placeholder='{placeholder}'")
            
            # 寻找JavaScript中的API端点
            scripts = soup.find_all('script')
            api_patterns = [
                r'["\']https?://[^"\']*api[^"\']*["\']',
                r'["\']https?://[^"\']*search[^"\']*["\']',
                r'["\'][/]api[^"\']*["\']',
                r'["\'][/]search[^"\']*["\']',
                r'url\s*:\s*["\'][^"\']+["\']',
                r'fetch\s*\(\s*["\'][^"\']+["\']'
            ]
            
            found_apis = set()
            for script in scripts:
                if script.string:
                    for pattern in api_patterns:
                        matches = re.findall(pattern, script.string, re.IGNORECASE)
                        for match in matches:
                            # 清理匹配结果
                            clean_url = match.strip('"\'')
                            if clean_url and not clean_url.startswith('data:'):
                                found_apis.add(clean_url)
            
            if found_apis:
                logger.success("在JavaScript中发现可能的API端点:")
                for api in sorted(found_apis):
                    logger.info(f"  {api}")
            
            return soup
            
        except Exception as e:
            logger.error(f"分析主页失败: {e}")
            return None
    
    def find_search_mechanism(self, soup):
        """寻找搜索机制"""
        logger.info("\n=== 寻找搜索机制 ===")
        
        if not soup:
            return []
        
        search_methods = []
        
        # 方法1: 分析搜索表单
        search_forms = soup.find_all('form', class_=lambda x: x and 'search' in ' '.join(x).lower() if x else False)
        if not search_forms:
            # 寻找包含搜索输入框的表单
            search_inputs = soup.find_all('input', {'name': lambda x: x and 'search' in x.lower() if x else False})
            search_inputs.extend(soup.find_all('input', {'class': lambda x: x and any('search' in cls for cls in x) if x else False}))
            
            for inp in search_inputs:
                form = inp.find_parent('form')
                if form and form not in search_forms:
                    search_forms.append(form)
        
        for form in search_forms:
            action = form.get('action', '')
            method = form.get('method', 'GET').upper()
            
            # 构建完整的action URL
            if action:
                if action.startswith('/'):
                    full_action = urljoin(self.base_url, action)
                elif action.startswith('http'):
                    full_action = action
                else:
                    full_action = urljoin(self.base_url + '/', action)
            else:
                full_action = self.base_url
            
            search_methods.append({
                'type': 'form',
                'method': method,
                'action': full_action,
                'form': form
            })
            
            logger.info(f"发现搜索表单: {method} {full_action}")
        
        # 方法2: 测试常见搜索端点
        common_endpoints = [
            '/search',
            '/api/search',
            '/s',
            '/find',
            '/query'
        ]
        
        for endpoint in common_endpoints:
            test_url = self.base_url + endpoint
            search_methods.append({
                'type': 'endpoint',
                'method': 'GET',
                'action': test_url + '?q={keyword}'
            })
        
        return search_methods
    
    def test_search_methods(self, search_methods):
        """测试搜索方法"""
        logger.info("\n=== 测试搜索方法 ===")
        
        test_keyword = "test"
        successful_methods = []
        
        for method_info in search_methods:
            logger.info(f"\n测试: {method_info['method']} {method_info['action']}")
            
            try:
                if method_info['type'] == 'form':
                    # 分析表单参数
                    form = method_info['form']
                    data = {}
                    
                    for inp in form.find_all(['input', 'select', 'textarea']):
                        name = inp.get('name')
                        if name:
                            if inp.get('type') == 'hidden':
                                data[name] = inp.get('value', '')
                            elif 'search' in name.lower() or 'keyword' in name.lower() or 'q' in name.lower():
                                data[name] = test_keyword
                            elif inp.get('type') in ['text', 'search']:
                                data[name] = test_keyword
                    
                    logger.info(f"  表单数据: {data}")
                    
                    if method_info['method'] == 'POST':
                        response = self.session.post(method_info['action'], data=data, timeout=10)
                    else:
                        response = self.session.get(method_info['action'], params=data, timeout=10)
                
                else:  # endpoint
                    test_url = method_info['action'].replace('{keyword}', test_keyword)
                    response = self.session.get(test_url, timeout=10)
                
                logger.info(f"  状态码: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'json' in content_type:
                        try:
                            data = response.json()
                            logger.success(f"  ✓ JSON响应成功: {str(data)[:100]}...")
                            successful_methods.append({
                                **method_info,
                                'response_type': 'json',
                                'test_response': data
                            })
                        except:
                            logger.warning("  JSON解析失败")
                    else:
                        # HTML响应
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 检查是否有搜索结果
                        possible_results = soup.find_all(['div', 'li', 'article'], 
                                                       class_=lambda x: x and any(word in ' '.join(x).lower() 
                                                       for word in ['item', 'result', 'card', 'anime', 'show']) if x else False)
                        
                        if possible_results:
                            logger.success(f"  ✓ HTML搜索页面，找到 {len(possible_results)} 个可能的结果容器")
                            successful_methods.append({
                                **method_info,
                                'response_type': 'html',
                                'result_containers': len(possible_results)
                            })
                        else:
                            logger.warning("  HTML页面，但未找到明显的搜索结果")
                
                elif response.status_code == 403:
                    logger.warning("  403 Forbidden - 可能需要额外的认证或headers")
                elif response.status_code == 404:
                    logger.warning("  404 Not Found - 端点不存在")
                else:
                    logger.warning(f"  其他错误: {response.status_code}")
                
                time.sleep(1)  # 避免请求过快
                
            except Exception as e:
                logger.error(f"  请求失败: {e}")
        
        return successful_methods
    
    def analyze_show_page_structure(self):
        """分析动漫详情页结构"""
        logger.info("\n=== 分析动漫详情页结构 ===")
        
        # 基于之前发现的链接格式，尝试访问一个动漫页面
        test_urls = [
            f"{self.base_url}/show/1",
            f"{self.base_url}/show/2", 
            f"{self.base_url}/show/100"
        ]
        
        for test_url in test_urls:
            logger.info(f"测试动漫页面: {test_url}")
            
            try:
                response = self.session.get(test_url, timeout=10)
                logger.info(f"  状态码: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 寻找剧集列表
                    episode_containers = soup.find_all(['div', 'ul', 'ol'], 
                                                     class_=lambda x: x and any(word in ' '.join(x).lower() 
                                                     for word in ['episode', 'ep', 'playlist', 'video']) if x else False)
                    
                    if episode_containers:
                        logger.success(f"  找到 {len(episode_containers)} 个可能的剧集容器")
                        
                        for i, container in enumerate(episode_containers[:2]):
                            logger.info(f"    容器 {i+1}: class={container.get('class', [])}")
                            
                            # 寻找容器内的链接
                            links = container.find_all('a')
                            if links:
                                logger.info(f"      包含 {len(links)} 个链接")
                                for j, link in enumerate(links[:3]):
                                    href = link.get('href', '')
                                    text = link.get_text(strip=True)
                                    logger.info(f"        链接 {j+1}: {href} - {text[:30]}")
                    
                    return soup
                    
            except Exception as e:
                logger.error(f"  访问失败: {e}")
        
        return None
    
    def generate_config_recommendations(self, successful_methods):
        """生成配置建议"""
        logger.info("\n=== 配置建议 ===")
        
        if not successful_methods:
            logger.warning("未找到有效的搜索方法，建议:")
            logger.info("1. 检查网站是否需要登录")
            logger.info("2. 查看网站是否使用JavaScript动态加载")
            logger.info("3. 尝试使用Selenium等工具模拟浏览器")
            return
        
        for i, method in enumerate(successful_methods):
            logger.success(f"\n方法 {i+1}:")
            logger.info(f"  类型: {method['type']}")
            logger.info(f"  HTTP方法: {method['method']}")
            logger.info(f"  URL: {method['action']}")
            
            if method['response_type'] == 'json':
                logger.info("  响应类型: JSON API")
                logger.info("  建议: 使用API接口，可能需要自定义解析逻辑")
            else:
                logger.info("  响应类型: HTML页面")
                logger.info("  建议: 使用现有的CSS选择器配置")
    
    def run_full_analysis(self):
        """运行完整分析"""
        logger.info("🔍 开始完整的网站分析")
        logger.info("=" * 60)
        
        # 1. 分析主页
        soup = self.analyze_main_page()
        
        # 2. 寻找搜索机制
        search_methods = self.find_search_mechanism(soup)
        
        # 3. 测试搜索方法
        successful_methods = self.test_search_methods(search_methods)
        
        # 4. 分析动漫页面结构
        self.analyze_show_page_structure()
        
        # 5. 生成配置建议
        self.generate_config_recommendations(successful_methods)
        
        logger.info("\n" + "=" * 60)
        logger.success("分析完成！")
        
        return successful_methods


def main():
    analyzer = GirigiriloveAnalyzer()
    successful_methods = analyzer.run_full_analysis()
    
    if successful_methods:
        logger.info("\n下一步: 根据成功的方法创建爬虫配置")
    else:
        logger.info("\n下一步: 考虑使用更高级的工具或手动分析网站")


if __name__ == "__main__":
    main()