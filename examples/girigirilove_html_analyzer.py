#!/usr/bin/env python3
"""
girigirilove HTML结构深度分析工具
用于确定正确的CSS选择器
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from web_scraper.utils.logger import logger


def analyze_search_page_html():
    """深度分析搜索页面的HTML结构"""
    logger.info("🔍 深度分析搜索页面HTML结构")
    logger.info("=" * 60)
    
    # 使用已知可工作的URL
    test_url = "https://anime.girigirilove.com/search/-------------/?wd=进击的巨人"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        logger.info(f"请求URL: {test_url}")
        response = requests.get(test_url, headers=headers, timeout=15)
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容长度: {len(response.text)} 字符")
        
        if response.status_code != 200:
            logger.error("页面访问失败")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 查找所有可能的列表容器
        logger.info("\n=== 1. 分析页面结构 ===")
        
        # 查找常见的列表/容器元素
        containers = {
            'ul elements': soup.find_all('ul'),
            'div with class containing "list"': soup.find_all('div', class_=lambda x: x and 'list' in ' '.join(x).lower() if x else False),
            'div with class containing "mac"': soup.find_all('div', class_=lambda x: x and 'mac' in ' '.join(x).lower() if x else False),
            'div with class containing "item"': soup.find_all('div', class_=lambda x: x and 'item' in ' '.join(x).lower() if x else False),
            'div with class containing "card"': soup.find_all('div', class_=lambda x: x and 'card' in ' '.join(x).lower() if x else False),
            'li elements': soup.find_all('li'),
        }
        
        for container_type, elements in containers.items():
            if elements:
                logger.info(f"\n{container_type}: {len(elements)} 个")
                for i, elem in enumerate(elements[:3]):  # 只显示前3个
                    classes = elem.get('class', [])
                    logger.info(f"  {i+1}. class: {classes}")
                    
                    # 显示元素的前100个字符的文本内容
                    text = elem.get_text(strip=True)
                    if text:
                        logger.info(f"     text: {text[:100]}...")
                    
                    # 查找内部的链接
                    links = elem.find_all('a', limit=3)
                    if links:
                        logger.info(f"     包含 {len(elem.find_all('a'))} 个链接:")
                        for j, link in enumerate(links):
                            href = link.get('href', '')
                            link_text = link.get_text(strip=True)
                            logger.info(f"       链接{j+1}: {href} - {link_text[:30]}")
        
        # 2. 查找所有链接
        logger.info("\n=== 2. 分析所有链接 ===")
        all_links = soup.find_all('a')
        logger.info(f"页面总计 {len(all_links)} 个链接")
        
        # 分类链接
        anime_links = []
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # 寻找可能的动漫链接
            if href and any(pattern in href for pattern in ['/show/', '/v/', '/anime/', '/detail/']):
                anime_links.append((href, text))
        
        if anime_links:
            logger.success(f"找到 {len(anime_links)} 个可能的动漫链接:")
            for i, (href, text) in enumerate(anime_links[:10]):  # 显示前10个
                logger.info(f"  {i+1}. {href} - {text[:50]}")
        
        # 3. 分析页面中的类名
        logger.info("\n=== 3. 分析所有CSS类名 ===")
        all_classes = set()
        for elem in soup.find_all(class_=True):
            classes = elem.get('class', [])
            all_classes.update(classes)
        
        # 过滤出可能相关的类名
        relevant_classes = [cls for cls in all_classes if any(keyword in cls.lower() for keyword in 
                           ['list', 'item', 'card', 'title', 'name', 'anime', 'show', 'video', 'mac'])]
        
        if relevant_classes:
            logger.info("找到相关的CSS类名:")
            for cls in sorted(relevant_classes):
                elements_with_class = soup.find_all(class_=cls)
                logger.info(f"  .{cls} ({len(elements_with_class)} 个元素)")
        
        # 4. 生成推荐的选择器
        logger.info("\n=== 4. 推荐的选择器配置 ===")
        
        recommendations = []
        
        # 基于找到的动漫链接推荐选择器
        if anime_links:
            sample_link = anime_links[0][0]
            parent_elements = soup.find_all('a', href=sample_link)
            if parent_elements:
                parent = parent_elements[0].find_parent()
                if parent:
                    parent_classes = parent.get('class', [])
                    if parent_classes:
                        recommendations.append(f"subject_selector: .{' .'.join(parent_classes)}")
                        recommendations.append(f"name_selector: a")  
                        recommendations.append(f"url_selector: a")
        
        # 基于找到的类名推荐选择器
        for cls in relevant_classes:
            if 'list' in cls.lower():
                recommendations.append(f"可能的容器: .{cls}")
            elif 'title' in cls.lower():
                recommendations.append(f"可能的标题: .{cls}")
            elif 'item' in cls.lower():
                recommendations.append(f"可能的项目: .{cls}")
        
        if recommendations:
            logger.success("推荐的选择器:")
            for rec in recommendations:
                logger.info(f"  {rec}")
        
        # 5. 输出页面片段用于手动分析
        logger.info("\n=== 5. 页面HTML片段 (用于手动分析) ===")
        
        # 寻找最有可能包含搜索结果的部分
        main_content = soup.find('main') or soup.find('div', class_=lambda x: x and 'main' in ' '.join(x).lower() if x else False)
        if main_content:
            logger.info("找到主要内容区域，HTML片段:")
            logger.info("```html")
            print(main_content.prettify()[:2000] + "..." if len(str(main_content)) > 2000 else main_content.prettify())
            logger.info("```")
        
        return soup
        
    except Exception as e:
        logger.error(f"分析HTML时出错: {e}")
        return None


def test_selector_candidates(soup):
    """测试候选选择器"""
    if not soup:
        return
        
    logger.info("\n=== 6. 测试候选选择器 ===")
    
    # 候选选择器列表
    selector_candidates = [
        # 基于常见模式
        (".mac-list li", ".mac-list-title", "a"),
        (".mac-list .mac-item", ".title", "a"), 
        ("ul.mac-list li", "a", "a"),
        (".list-item", ".title", "a"),
        (".search-result", ".title", "a"),
        (".anime-item", ".name", "a"),
        
        # 更通用的选择器
        ("li", "a", "a"),
        (".item", "a", "a"),  
        ("article", "h2 a", "h2 a"),
        (".card", ".title a", ".title a"),
    ]
    
    for i, (container_sel, title_sel, url_sel) in enumerate(selector_candidates):
        logger.info(f"\n测试选择器组合 {i+1}:")
        logger.info(f"  容器: {container_sel}")
        logger.info(f"  标题: {title_sel}")
        logger.info(f"  链接: {url_sel}")
        
        try:
            containers = soup.select(container_sel)
            logger.info(f"  找到容器: {len(containers)} 个")
            
            if containers:
                # 测试前几个容器
                valid_results = 0
                for j, container in enumerate(containers[:5]):
                    title_elem = container.select_one(title_sel)
                    url_elem = container.select_one(url_sel)
                    
                    if title_elem and url_elem:
                        title_text = title_elem.get_text(strip=True)
                        url_href = url_elem.get('href', '')
                        
                        if title_text and url_href:
                            valid_results += 1
                            logger.info(f"    结果{j+1}: {title_text[:30]} -> {url_href}")
                
                if valid_results > 0:
                    logger.success(f"  ✓ 此选择器组合有效! 找到 {valid_results} 个有效结果")
                    logger.info("  建议使用此选择器配置")
                    
                    return {
                        'subject_selector': container_sel,
                        'name_selector': title_sel,
                        'url_selector': url_sel,
                        'valid_results': valid_results
                    }
                else:
                    logger.warning("  ✗ 此选择器无有效结果")
        
        except Exception as e:
            logger.error(f"  ✗ 选择器错误: {e}")
    
    return None


def main():
    """主函数"""
    logger.info("🎯 girigirilove HTML深度分析")
    
    # 分析HTML结构
    soup = analyze_search_page_html()
    
    # 测试候选选择器
    if soup:
        best_selector = test_selector_candidates(soup)
        
        if best_selector:
            logger.success(f"\n🎉 找到最佳选择器配置:")
            logger.info(f"subject_selector = '{best_selector['subject_selector']}'")
            logger.info(f"name_selector = '{best_selector['name_selector']}'") 
            logger.info(f"url_selector = '{best_selector['url_selector']}'")
            logger.info(f"有效结果数: {best_selector['valid_results']}")
        else:
            logger.warning("未找到有效的选择器配置，请手动检查HTML结构")


if __name__ == "__main__":
    main()