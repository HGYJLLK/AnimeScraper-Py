#!/usr/bin/env python3
"""
girigirilove 可工作配置
基于真实URL格式和HTML结构分析
"""

import sys
import os
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web_scraper.core import SelectorMediaSource
from web_scraper.models import (
    SelectorSearchConfig, MediaFetchRequest, EpisodeSort,
    SelectorSubjectFormatConfig, SelectorChannelFormatConfig, MatchVideoConfig
)
from web_scraper.utils.logger import logger


def create_working_config():
    """
    基于发现的真实格式创建配置
    URL格式: https://anime.girigirilove.com/search/-------------/?wd=进击的巨人
    """
    return SelectorSearchConfig(
        # 真实的搜索URL格式
        search_url="https://anime.girigirilove.com/search/-------------/?wd={keyword}",
        
        # 搜索设置
        search_use_only_first_word=False,  # 保留完整关键词
        search_remove_special=False,       # 保留特殊字符，因为是查询参数
        search_use_subject_names_count=2,  # 尝试多个名称
        
        # 请求设置
        request_interval_seconds=3.0,      # 3秒间隔
        
        # 主题格式配置 - 基于分析的HTML结构
        subject_format_config=SelectorSubjectFormatConfig(
            # 搜索结果项容器
            subject_selector=".mac-list li, .mac-list .mac-item",
            # 动漫标题选择器
            name_selector=".mac-list-title a, .mac-list-title, .title a, .title",
            # 详情页链接选择器  
            url_selector=".mac-list-title a, a[href*='/show/'], a[href*='/G']"
        ),
        
        # 频道格式配置 - 剧集页面
        channel_format_config=SelectorChannelFormatConfig(
            # 剧集容器（需要进一步分析剧集页面）
            episode_selector=".mac-list-item, .episode-item, .play-list li, .playlist li",
            # 剧集标题
            name_selector=".mac-list-title, .episode-title, .title, a",
            # 播放链接
            url_selector="a, .play-btn, .episode-link"
        ),
        
        # 视频匹配配置
        match_video=MatchVideoConfig(
            enable_nested_url=True,
            match_video_url=r"(\.mp4|\.m3u8|/play/|/video/|stream|watch)",
            cookies="",
        ),
        
        default_resolution="1080P", 
        default_subtitle_language="CHS"
    )


class GirigiriloveMediaSource(SelectorMediaSource):
    """
    girigirilove 专用媒体源
    处理URL编码和特殊格式
    """
    
    def __init__(self, media_source_id: str, config: SelectorSearchConfig, session=None):
        super().__init__(media_source_id, config, session)
    
    def _encode_search_keyword(self, keyword):
        """对搜索关键词进行URL编码"""
        # URL编码中文字符
        encoded = quote(keyword, safe='')
        logger.debug(f"关键词编码: {keyword} -> {encoded}")
        return encoded
    
    async def search(self, search_config, query):
        """覆盖搜索方法处理URL编码"""
        original_url = search_config.search_url
        
        # 对关键词进行URL编码
        encoded_keyword = self._encode_search_keyword(query.subject_name)
        search_config.search_url = original_url.replace('{keyword}', encoded_keyword)
        
        logger.info(f"搜索URL: {search_config.search_url}")
        
        try:
            result = await super().search(search_config, query)
            return result
        finally:
            # 恢复原始URL
            search_config.search_url = original_url


def test_working_config():
    """测试可工作的配置"""
    logger.info("🎬 测试 girigirilove 可工作配置")
    logger.info("=" * 60)
    
    config = create_working_config()
    source = GirigiriloveMediaSource("girigirilove-working", config)
    
    # 测试连接
    logger.info("测试基本连接...")
    connection_status = source.check_connection()
    logger.info(f"连接状态: {connection_status}")
    
    if connection_status != "SUCCESS":
        logger.warning("基本连接失败，但可能是搜索URL格式问题，继续测试搜索功能")
    
    # 测试搜索功能
    test_queries = [
        "进击的巨人",
        "鬼灭之刃",
        "海贼王"
    ]
    
    for query in test_queries:
        logger.info(f"\n=== 搜索测试: {query} ===")
        
        # 测试URL编码
        encoded = source._encode_search_keyword(query)
        test_url = config.search_url.replace('{keyword}', encoded)
        logger.info(f"测试URL: {test_url}")
        
        # 创建搜索请求
        request = MediaFetchRequest(
            subject_names=[query],
            episode_sort=EpisodeSort(1)
        )
        
        try:
            logger.info("执行搜索...")
            matches = list(source.fetch(request))
            
            if matches:
                logger.success(f"✓ 找到 {len(matches)} 个结果:")
                for i, match in enumerate(matches[:3]):
                    logger.info(f"  {i+1}. {match.media.original_title}")
                    logger.info(f"     URL: {match.media.download.url}")
                    
                # 找到结果就停止，避免过多请求
                logger.success("搜索成功！配置工作正常。")
                break
                
            else:
                logger.warning(f"未找到 '{query}' 的搜索结果")
                logger.info("可能原因:")
                logger.info("1. CSS选择器需要调整")
                logger.info("2. 搜索关键词在网站上不存在")
                logger.info("3. 网站返回格式与预期不符")
                
        except Exception as e:
            logger.error(f"搜索 '{query}' 时出错: {e}")
            logger.info("继续测试下一个关键词...")
    
    logger.info(f"\n{'='*60}")
    logger.success("配置测试完成！")


def debug_search_page():
    """调试搜索页面结构"""
    logger.info("\n=== 调试搜索页面结构 ===")
    
    import requests
    from bs4 import BeautifulSoup
    
    # 测试搜索页面
    test_url = "https://anime.girigirilove.com/search/-------------/?wd=进击的巨人"
    
    logger.info(f"获取页面: {test_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
        }
        
        response = requests.get(test_url, headers=headers, timeout=15)
        logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找可能的搜索结果容器
            possible_containers = [
                soup.find_all(class_=lambda x: x and 'mac-list' in x if x else False),
                soup.find_all(class_=lambda x: x and 'list' in x if x else False),
                soup.find_all(class_=lambda x: x and 'item' in x if x else False),
                soup.find_all('li'),
                soup.find_all(class_=lambda x: x and 'card' in x if x else False)
            ]
            
            for i, containers in enumerate(possible_containers):
                if containers:
                    logger.info(f"找到容器类型 {i+1}: {len(containers)} 个元素")
                    for j, container in enumerate(containers[:2]):
                        classes = container.get('class', [])
                        logger.info(f"  容器 {j+1}: {classes}")
                        
                        # 查找其中的链接和文本
                        links = container.find_all('a')
                        if links:
                            for k, link in enumerate(links[:2]):
                                href = link.get('href', '')
                                text = link.get_text(strip=True)
                                logger.info(f"    链接 {k+1}: {href} - {text[:30]}")
            
            # 查找标题相关元素
            title_elements = soup.find_all(class_=lambda x: x and 'title' in ' '.join(x).lower() if x else False)
            if title_elements:
                logger.info(f"找到 {len(title_elements)} 个标题元素:")
                for i, elem in enumerate(title_elements[:3]):
                    classes = elem.get('class', [])
                    text = elem.get_text(strip=True)
                    logger.info(f"  标题 {i+1}: {classes} - {text[:50]}")
            
        else:
            logger.error(f"页面访问失败: {response.status_code}")
            
    except Exception as e:
        logger.error(f"调试页面时出错: {e}")


def main():
    """主函数"""
    logger.info("🚀 girigirilove 完整测试")
    logger.info("基于发现的真实URL格式进行测试")
    
    # 首先调试页面结构
    debug_search_page()
    
    # 然后测试配置
    test_working_config()


if __name__ == "__main__":
    main()