#!/usr/bin/env python3
"""
girigirilove 播放URL获取配置
目标：获取实际的播放URL而不是分类页面
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


def create_playurl_config():
    """
    专门用于获取播放URL的配置
    修复占位符问题，专注于获取实际播放链接
    """
    return SelectorSearchConfig(
        # 正确的URL格式：保留占位符 + 查询参数
        search_url="https://anime.girigirilove.com/search/-------------/?wd={keyword}",
        
        # 搜索设置
        search_use_only_first_word=False,
        search_remove_special=False, 
        search_use_subject_names_count=1,  # 先测试单个名称
        
        # 请求设置
        request_interval_seconds=2.0,
        
        # 主题格式配置 - 专门寻找播放页面链接
        subject_format_config=SelectorSubjectFormatConfig(
            # 寻找包含播放链接的容器
            subject_selector="li:has(a[href*='/GV']), .public-list-box:has(a[href*='/GV']), li:has(a[href*='/show/'])",
            # 获取链接文本作为标题
            name_selector="a",
            # 获取实际的播放页面链接
            url_selector="a[href*='/GV'], a[href*='/show/']"
        ),
        
        # 频道格式配置 - 剧集页面内的具体播放链接
        channel_format_config=SelectorChannelFormatConfig(
            # 剧集页面中的播放链接容器
            episode_selector=".public-list-box, .play-list li, .episode-list li, li",
            # 剧集名称
            name_selector="a, .title, .episode-name",
            # 实际播放链接
            url_selector="a[href*='/play/'], a[href*='/watch/'], a[href*='/video/'], a"
        ),
        
        # 视频匹配配置 - 匹配真实的播放URL
        match_video=MatchVideoConfig(
            enable_nested_url=True,
            # 匹配播放相关的URL模式
            match_video_url=r"(\.mp4|\.m3u8|/play/|/watch/|/video/|stream|player|/GV\d+/)",
            cookies="",
        ),
        
        default_resolution="1080P",
        default_subtitle_language="CHS"
    )


class PlayUrlGirigiriloveSource(SelectorMediaSource):
    """
    专门获取播放URL的数据源
    修复URL格式问题，专注播放链接提取
    """
    
    def __init__(self, media_source_id: str, config: SelectorSearchConfig, session=None):
        super().__init__(media_source_id, config, session)
    
    def _build_correct_search_url(self, keyword: str) -> str:
        """
        构建正确的搜索URL
        确保保留占位符并使用查询参数
        """
        # URL编码关键词
        encoded_keyword = quote(keyword)
        
        # 使用正确的格式：保留占位符 + 查询参数
        search_url = f"https://anime.girigirilove.com/search/-------------/?wd={encoded_keyword}"
        
        return search_url
    
    def _is_play_url(self, url: str) -> bool:
        """
        判断是否是播放URL而不是分类页面
        """
        if not url:
            return False
            
        # 播放URL的特征
        play_patterns = [
            '/GV',          # GV开头的动漫ID
            '/play/',       # 播放页面
            '/watch/',      # 观看页面
            '/video/',      # 视频页面
            '/episode/',    # 剧集页面
        ]
        
        for pattern in play_patterns:
            if pattern in url:
                return True
        
        # 排除分类页面
        category_patterns = [
            '/show/2-----------',  # 日番分类
            '/show/21-----------', # 剧场版分类
            '/label/',             # 标签页
        ]
        
        for pattern in category_patterns:
            if pattern in url:
                return False
                
        return True
    
    async def search(self, search_config, query):
        """覆盖搜索方法，确保URL格式正确"""
        # 构建正确的搜索URL
        correct_search_url = self._build_correct_search_url(query.subject_name)
        
        # 临时替换配置中的URL
        original_url = search_config.search_url
        search_config.search_url = correct_search_url
        
        logger.info(f"使用正确的搜索URL: {search_config.search_url}")
        
        try:
            # 调用父类搜索
            results = await super().search(search_config, query)
            
            # 过滤出播放URL
            play_results = []
            for media in results:
                url = media.download.url if media.download else ""
                
                if self._is_play_url(url):
                    play_results.append(media)
                    logger.debug(f"✓ 播放URL: {media.original_title} -> {url}")
                else:
                    logger.debug(f"✗ 跳过分类页面: {media.original_title} -> {url}")
            
            logger.info(f"找到播放URL: {len(play_results)}/{len(results)}")
            return play_results
            
        finally:
            # 恢复原始URL
            search_config.search_url = original_url


def test_playurl_extraction():
    """测试播放URL提取功能"""
    logger.info("🎯 测试播放URL提取功能")
    logger.info("=" * 60)
    
    config = create_playurl_config()
    source = PlayUrlGirigiriloveSource("girigirilove-playurl", config)
    
    # 测试多个动漫
    test_queries = [
        "进击的巨人",
        "鬼灭之刃", 
        "火影忍者",
        "海贼王",
        "死亡笔记"  # 从之前的结果看，这个可能存在
    ]
    
    for query in test_queries:
        logger.info(f"\n=== 搜索播放URL: {query} ===")
        
        # 手动构建测试URL验证格式
        test_url = source._build_correct_search_url(query)
        logger.info(f"测试URL: {test_url}")
        
        request = MediaFetchRequest(
            subject_names=[query],
            episode_sort=EpisodeSort(1)
        )
        
        try:
            matches = list(source.fetch(request))
            
            if matches:
                logger.success(f"✅ 找到 {len(matches)} 个播放链接:")
                for i, match in enumerate(matches[:5]):  # 显示前5个
                    title = match.media.original_title
                    url = match.media.download.url if match.media.download else ""
                    logger.info(f"  {i+1}. {title}")
                    logger.info(f"     播放URL: {url}")
                
                # 找到播放链接就停止测试
                logger.success(f"🎉 成功获取 {query} 的播放链接!")
                return True
                
            else:
                logger.warning(f"未找到 '{query}' 的播放链接")
                
        except Exception as e:
            logger.error(f"搜索 '{query}' 时出错: {e}")
    
    logger.warning("❌ 未能找到任何播放链接")
    return False


def analyze_play_url_issue():
    """分析播放URL获取问题"""
    logger.info("\n=== 播放URL获取问题分析 ===")
    
    issues = [
        "1. 网站搜索返回的可能是分类页面而不是具体动漫",
        "2. 需要进一步访问分类页面才能获取具体的播放链接",
        "3. 播放链接可能需要二次解析（先获取动漫页面，再获取播放链接）",
        "4. 网站可能需要特定的搜索关键词才有结果"
    ]
    
    for issue in issues:
        logger.info(issue)
    
    logger.info("\n解决方案:")
    solutions = [
        "1. 尝试访问分类页面（如2025年日番）获取具体动漫列表",
        "2. 实现两阶段搜索：搜索 -> 动漫页面 -> 播放链接",
        "3. 分析具体的动漫详情页面结构", 
        "4. 寻找网站中确实存在的动漫进行测试"
    ]
    
    for solution in solutions:
        logger.info(solution)


def test_category_page():
    """测试直接访问分类页面获取播放链接"""
    logger.info("\n=== 测试分类页面播放链接提取 ===")
    
    # 基于之前的成功结果，尝试访问分类页面
    category_urls = [
        "https://anime.girigirilove.com/show/2-----------2025/",  # 2025年日番
        "https://anime.girigirilove.com/show/2-----------2024/",  # 2024年日番
    ]
    
    for category_url in category_urls:
        logger.info(f"\n访问分类页面: {category_url}")
        
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(category_url, headers=headers, timeout=15)
            logger.info(f"响应状态: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 寻找具体的动漫链接
                anime_links = soup.find_all('a', href=lambda x: x and '/GV' in x if x else False)
                
                if anime_links:
                    logger.success(f"找到 {len(anime_links)} 个动漫播放链接:")
                    for i, link in enumerate(anime_links[:10]):  # 显示前10个
                        href = link.get('href', '')
                        text = link.get_text(strip=True)
                        logger.info(f"  {i+1}. {text} -> {href}")
                    
                    return True
                else:
                    logger.warning("在分类页面中未找到播放链接")
            
        except Exception as e:
            logger.error(f"访问分类页面时出错: {e}")
    
    return False


def main():
    """主函数"""
    logger.info("🎯 girigirilove 播放URL获取专用配置")
    logger.info("目标：获取实际的播放URL而不是分类页面")
    logger.info("=" * 60)
    
    # 测试播放URL提取
    success = test_playurl_extraction()
    
    if not success:
        # 如果直接搜索失败，尝试访问分类页面
        logger.info("\n直接搜索未成功，尝试分类页面方法...")
        test_category_page()
    
    # 分析问题
    analyze_play_url_issue()
    
    logger.info("\n" + "=" * 60)
    logger.success("播放URL配置测试完成！")
    logger.info("下一步建议：")
    logger.info("1. 如果找到播放链接，进一步解析剧集页面")
    logger.info("2. 如果没找到，考虑直接分析动漫分类页面")
    logger.info("3. 实现两阶段爬取：分类页面 -> 播放页面")


if __name__ == "__main__":
    main()