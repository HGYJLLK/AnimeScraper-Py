#!/usr/bin/env python3
"""
手动调试 girigirilove 网站
使用更详细的方法来分析网站结构
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from web_scraper.utils.logger import logger


def test_basic_access():
    """测试基本访问"""
    logger.info("=== 测试基本网站访问 ===")
    
    # 模拟真实浏览器的请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        logger.info("尝试访问主页...")
        response = session.get("https://anime.girigirilove.com/", timeout=15)
        logger.info(f"主页状态码: {response.status_code}")
        
        if response.status_code == 200:
            logger.success("主页访问成功！")
            
            # 分析页面内容
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找搜索相关元素
            search_elements = soup.find_all(['input', 'form'], class_=lambda x: x and 'search' in x.lower() if x else False)
            if search_elements:
                logger.info("找到可能的搜索元素:")
                for elem in search_elements[:3]:
                    logger.info(f"  {elem.name}: {elem.get('class', [])} - {elem.get('action', '')}")
            
            # 查找可能的动漫链接
            anime_links = soup.find_all('a', href=lambda x: x and ('anime' in x or 'show' in x or '/v/' in x) if x else False)
            if anime_links:
                logger.info("找到可能的动漫链接:")
                for link in anime_links[:5]:
                    logger.info(f"  {link.get('href')} - {link.get_text(strip=True)[:30]}")
            
            return True, session
            
        else:
            logger.error(f"主页访问失败，状态码: {response.status_code}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求失败: {e}")
        return False, None


def find_search_functionality(session):
    """寻找搜索功能"""
    logger.info("\n=== 寻找搜索功能 ===")
    
    # 尝试不同的搜索URL模式
    search_patterns = [
        "https://anime.girigirilove.com/search?q=test",
        "https://anime.girigirilove.com/search/test",
        "https://anime.girigirilove.com/s/test",
        "https://anime.girigirilove.com/api/search?keyword=test",
        "https://anime.girigirilove.com/search.php?keyword=test"
    ]
    
    for pattern in search_patterns:
        logger.info(f"尝试搜索URL: {pattern}")
        
        try:
            response = session.get(pattern, timeout=10)
            logger.info(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 检查响应内容
                content_type = response.headers.get('content-type', '')
                if 'json' in content_type:
                    logger.success("  发现JSON API接口！")
                    try:
                        data = response.json()
                        logger.info(f"  JSON数据示例: {str(data)[:200]}")
                    except:
                        logger.info("  无法解析JSON数据")
                else:
                    logger.success("  发现HTML搜索页面！")
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 分析搜索结果结构
                    possible_containers = soup.find_all(['div', 'li', 'article'], 
                                                       class_=lambda x: x and any(word in x.lower() 
                                                       for word in ['item', 'card', 'result', 'anime', 'video']) if x else False)
                    
                    if possible_containers:
                        logger.info(f"  找到 {len(possible_containers)} 个可能的结果容器")
                        for i, container in enumerate(possible_containers[:3]):
                            classes = container.get('class', [])
                            logger.info(f"    容器 {i+1}: {classes}")
                return pattern
            elif response.status_code == 404:
                logger.warning("  页面不存在")
            else:
                logger.warning(f"  其他错误: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"  请求失败: {e}")
        
        time.sleep(1)  # 避免请求过快
    
    logger.warning("未找到可用的搜索接口")
    return None


def analyze_page_structure():
    """分析页面结构的手动方法"""
    logger.info("\n=== 页面结构分析指南 ===")
    
    steps = [
        "1. 打开浏览器，访问 https://anime.girigirilove.com/",
        "2. 打开开发者工具 (F12)",
        "3. 切换到 Network (网络) 标签",
        "4. 在网站上搜索 '进击的巨人' 或其他动漫",
        "5. 观察 Network 标签中的请求:",
        "   - 查找包含搜索关键词的请求",
        "   - 注意请求的URL格式",
        "   - 检查是否有AJAX/API请求",
        "6. 如果找到搜索请求，记录其URL格式",
        "7. 查看搜索结果页面的HTML源码:",
        "   - 右键 -> 查看页面源代码",
        "   - 或在开发者工具的Elements标签中查看",
        "8. 寻找每个动漫结果的HTML结构:",
        "   - 容器元素的class或id",
        "   - 标题元素的选择器",
        "   - 链接元素的选择器",
        "9. 点击进入一个动漫详情页",
        "10. 分析剧集列表的HTML结构",
        "11. 根据分析结果修改配置文件"
    ]
    
    for step in steps:
        if step.startswith(('1.', '2.', '3.', '4.', '9.', '11.')):
            logger.info(step)
        elif step.startswith('5.'):
            logger.warning(step)
        elif step.startswith(('6.', '7.', '8.', '10.')):
            logger.warning(step)
        else:
            logger.info(step)


def create_debug_config_template():
    """创建调试配置模板"""
    logger.info("\n=== 创建调试配置模板 ===")
    
    template = '''
# 基于你的分析结果，修改以下配置:

config = SelectorSearchConfig(
    # 第4步中发现的搜索URL格式
    search_url="在这里填入正确的搜索URL格式",  # 例如: https://site.com/search?q={keyword}
    
    # 搜索结果页面的选择器
    subject_format_config=SelectorSubjectFormatConfig(
        subject_selector="在这里填入结果容器的选择器",  # 例如: .anime-card, .search-result
        name_selector="在这里填入标题的选择器",        # 例如: .title, h3
        url_selector="在这里填入链接的选择器"          # 例如: a, .link
    ),
    
    # 剧集页面的选择器  
    channel_format_config=SelectorChannelFormatConfig(
        episode_selector="在这里填入剧集容器的选择器",  # 例如: .episode-item
        name_selector="在这里填入剧集标题的选择器",     # 例如: .ep-title  
        url_selector="在这里填入播放链接的选择器"       # 例如: .play-link
    )
)
'''
    
    logger.info("配置模板:")
    print(template)


def main():
    """主函数"""
    logger.info("🔍 girigirilove 网站手动调试工具")
    logger.info("=" * 50)
    
    # 测试基本访问
    success, session = test_basic_access()
    
    if success and session:
        # 寻找搜索功能
        search_url = find_search_functionality(session)
        if search_url:
            logger.success(f"找到可能的搜索URL: {search_url}")
    
    # 提供手动分析指南
    analyze_page_structure()
    
    # 提供配置模板
    create_debug_config_template()
    
    logger.info("\n" + "=" * 50)
    logger.success("调试工具运行完成！")
    logger.info("请按照指南手动分析网站结构，然后更新配置。")


if __name__ == "__main__":
    main()