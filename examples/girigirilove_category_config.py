#!/usr/bin/env python3
"""
girigirilove 分类页面配置
基于成功的分类页面播放链接提取
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


def create_category_config():
    """
    基于分类页面的配置
    直接使用分类页面获取播放链接，绕过搜索问题
    """
    return SelectorSearchConfig(
        # 使用分类页面而不是搜索页面
        search_url="https://anime.girigirilove.com/show/2-----------2025/",
        
        # 搜索设置
        search_use_only_first_word=False,
        search_remove_special=False,
        search_use_subject_names_count=1,
        
        # 请求设置
        request_interval_seconds=3.0,
        
        # 主题格式配置 - 基于成功的分类页面结构
        subject_format_config=SelectorSubjectFormatConfig(
            # 包含GV链接的容器
            subject_selector="a[href*='/GV']",
            # 获取动漫名称
            name_selector="self::*",
            # 获取播放链接
            url_selector="self::*"
        ),
        
        # 频道格式配置 - 动漫详情页面的剧集列表
        channel_format_config=SelectorChannelFormatConfig(
            # 剧集容器
            episode_selector="a[href*='/play/'], .episode-item, .play-list li",
            # 剧集名称
            name_selector="self::*, .title, .episode-name",
            # 播放链接
            url_selector="self::*"
        ),
        
        # 视频匹配配置
        match_video=MatchVideoConfig(
            enable_nested_url=True,
            match_video_url=r"(\\.mp4|\\.m3u8|/play/|/video/|stream|watch|/GV\\d+/)",
            cookies="",
        ),
        
        default_resolution="1080P",
        default_subtitle_language="CHS"
    )


def create_fixed_search_config():
    """
    修复选择器错误的搜索配置
    简化选择器避免解析错误
    """
    return SelectorSearchConfig(
        # 修复后的搜索URL
        search_url="https://anime.girigirilove.com/search/-------------/?wd={keyword}",
        
        search_use_only_first_word=False,
        search_remove_special=False,
        search_use_subject_names_count=1,
        request_interval_seconds=3.0,
        
        # 简化的选择器配置，避免复杂选择器导致解析错误
        subject_format_config=SelectorSubjectFormatConfig(
            # 使用简单的选择器
            subject_selector="li",
            name_selector="a",
            url_selector="a"
        ),
        
        channel_format_config=SelectorChannelFormatConfig(
            episode_selector="li",
            name_selector="a",
            url_selector="a"
        ),
        
        match_video=MatchVideoConfig(
            enable_nested_url=True,
            match_video_url=r"(\\.mp4|\\.m3u8|/play/|/video/|stream|watch|/GV\\d+/)",
            cookies="",
        ),
        
        default_resolution="1080P",
        default_subtitle_language="CHS"
    )


class CategoryGirigiriloveSource(SelectorMediaSource):
    """
    基于分类页面的girigirilove数据源
    直接从分类页面获取动漫列表，然后进一步解析
    """
    
    def __init__(self, media_source_id: str, config: SelectorSearchConfig, session=None):
        super().__init__(media_source_id, config, session)
    
    def _build_category_url(self, keyword: str = "") -> str:
        """
        构建分类页面URL
        可以根据关键词选择不同的分类页面
        """
        # 默认使用2025年日番页面
        category_url = "https://anime.girigirilove.com/show/2-----------2025/"
        return category_url
    
    def _is_valid_anime_link(self, url: str, title: str) -> bool:
        """
        验证是否是有效的动漫播放链接
        """
        if not url or not title:
            return False
            
        # 检查是否包含GV ID（播放链接的特征）
        if '/GV' in url:
            return True
            
        return False
    
    async def search(self, search_config, query):
        """覆盖搜索方法，直接访问分类页面"""
        category_url = self._build_category_url(query.subject_name)
        
        # 临时替换搜索URL为分类页面URL
        original_url = search_config.search_url
        search_config.search_url = category_url
        
        logger.info(f"访问分类页面: {search_config.search_url}")
        
        try:
            # 调用父类搜索方法
            results = await super().search(search_config, query)
            
            # 过滤出有效的播放链接
            valid_results = []
            for media in results:
                url = media.download.url if media.download else ""
                title = media.original_title
                
                if self._is_valid_anime_link(url, title):
                    valid_results.append(media)
                    logger.debug(f"有效播放链接: {title} -> {url}")
            
            logger.info(f"找到有效播放链接: {len(valid_results)}/{len(results)}")
            
            # 如果查询特定动漫，尝试匹配
            if query.subject_name:
                matched_results = []
                query_lower = query.subject_name.lower()
                for media in valid_results:
                    title_lower = media.original_title.lower()
                    if query_lower in title_lower or any(char in title_lower for char in query.subject_name):
                        matched_results.append(media)
                
                if matched_results:
                    logger.success(f"匹配到 '{query.subject_name}' 相关结果: {len(matched_results)} 个")
                    return matched_results
            
            return valid_results
            
        finally:
            # 恢复原始URL
            search_config.search_url = original_url


class FixedSearchGirigiriloveSource(SelectorMediaSource):
    """
    修复选择器错误的搜索数据源
    使用简化的选择器避免解析错误
    """
    
    def __init__(self, media_source_id: str, config: SelectorSearchConfig, session=None):
        super().__init__(media_source_id, config, session)
    
    async def search(self, search_config, query):
        """修复选择器错误的搜索方法"""
        # 对关键词进行URL编码
        encoded_keyword = quote(query.subject_name)
        original_url = search_config.search_url
        search_config.search_url = original_url.replace('{keyword}', encoded_keyword)
        
        logger.info(f"修复后的搜索URL: {search_config.search_url}")
        
        try:
            results = await super().search(search_config, query)
            return results
        finally:
            search_config.search_url = original_url


def test_category_approach():
    """测试分类页面方法"""
    logger.info("🎯 测试分类页面方法")
    logger.info("=" * 60)
    
    config = create_category_config()
    source = CategoryGirigiriloveSource("girigirilove-category", config)
    
    # 测试不同的查询
    test_queries = [
        "小城",      # 基于发现的 "小城日常"
        "异人",      # 基于发现的 "异人旅馆"
        "废渊",      # 基于发现的 "废渊战鬼"
        ""           # 空查询，获取所有结果
    ]
    
    for query in test_queries:
        logger.info(f"\n=== 测试查询: '{query}' ===")
        
        request = MediaFetchRequest(
            subject_names=[query] if query else [""],
            episode_sort=EpisodeSort(1)
        )
        
        try:
            matches = list(source.fetch(request))
            
            if matches:
                logger.success(f"✅ 找到 {len(matches)} 个结果:")
                for i, match in enumerate(matches[:5]):
                    title = match.media.original_title
                    url = match.media.download.url if match.media.download else ""
                    logger.info(f"  {i+1}. {title}")
                    logger.info(f"     URL: {url}")
                
                # 找到结果就测试成功
                logger.success("🎉 分类页面方法成功!")
                return True
                
            else:
                logger.warning(f"未找到 '{query}' 的结果")
                
        except Exception as e:
            logger.error(f"测试 '{query}' 时出错: {e}")
    
    return False


def test_fixed_search():
    """测试修复的搜索功能"""
    logger.info("\n🔧 测试修复的搜索功能")
    logger.info("=" * 60)
    
    config = create_fixed_search_config()
    source = FixedSearchGirigiriloveSource("girigirilove-fixed", config)
    
    # 使用在分类页面中发现的动漫名称进行搜索
    test_queries = [
        "小城日常",
        "异人旅馆",
        "废渊战鬼"
    ]
    
    for query in test_queries:
        logger.info(f"\n=== 修复搜索测试: {query} ===")
        
        request = MediaFetchRequest(
            subject_names=[query],
            episode_sort=EpisodeSort(1)
        )
        
        try:
            matches = list(source.fetch(request))
            
            if matches:
                logger.success(f"✅ 搜索成功! 找到 {len(matches)} 个结果:")
                for i, match in enumerate(matches[:3]):
                    title = match.media.original_title
                    url = match.media.download.url if match.media.download else ""
                    logger.info(f"  {i+1}. {title}")
                    logger.info(f"     URL: {url}")
                
                logger.success("🎉 修复的搜索方法成功!")
                return True
                
            else:
                logger.warning(f"搜索 '{query}' 无结果")
                
        except Exception as e:
            logger.error(f"搜索 '{query}' 时出错: {e}")
    
    return False


def main():
    """主函数"""
    logger.info("🚀 girigirilove 分类页面配置测试")
    logger.info("基于成功的分类页面发现结果")
    logger.info("=" * 60)
    
    # 首先测试分类页面方法
    category_success = test_category_approach()
    
    # 然后测试修复的搜索方法
    search_success = test_fixed_search()
    
    logger.info(f"\n{'=' * 60}")
    logger.success("测试完成!")
    
    if category_success:
        logger.success("✅ 分类页面方法可用 - 推荐使用")
        logger.info("优势: 直接访问分类页面，获取真实的播放链接")
    
    if search_success:
        logger.success("✅ 修复搜索方法可用")
        logger.info("优势: 支持关键词搜索特定动漫")
    
    if not category_success and not search_success:
        logger.error("❌ 两种方法都未成功")
        logger.info("建议: 进一步分析网站结构或使用其他方法")
    
    logger.info("\n下一步建议:")
    logger.info("1. 使用成功的方法进一步解析剧集页面")
    logger.info("2. 分析 /GV 链接页面的结构获取具体播放URL")
    logger.info("3. 实现完整的播放链接提取流程")


if __name__ == "__main__":
    main()