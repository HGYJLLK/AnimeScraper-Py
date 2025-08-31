#!/usr/bin/env python3
"""
你的网站配置 - 请根据实际情况修改
"""

from web_scraper.core import SelectorMediaSource
from web_scraper.models import (
    SelectorSearchConfig, MediaFetchRequest, EpisodeSort,
    SelectorSubjectFormatConfig, SelectorChannelFormatConfig
)
from web_scraper.utils.logger import logger

# 配置你的网站
config = SelectorSearchConfig(
    # TODO: 修改为你的搜索URL
    search_url="https://your-site.com/search?q={keyword}",
    
    # TODO: 根据你的网站修改选择器
    subject_format_config=SelectorSubjectFormatConfig(
        subject_selector=".search-result-item",  # 搜索结果容器
        name_selector=".anime-title",            # 动漫标题
        url_selector="a.detail-link"             # 详情页链接
    ),
    
    channel_format_config=SelectorChannelFormatConfig(
        episode_selector=".episode-item",        # 剧集容器
        name_selector=".episode-title",          # 剧集标题
        url_selector=".play-link"                # 播放链接
    ),
    
    # 可选设置
    request_interval_seconds=2.0,
    default_resolution="1080P",
    default_subtitle_language="CHS"
)

def test_configuration():
    """测试配置"""
    source = SelectorMediaSource("my-site", config)
    
    # 测试连接
    logger.info(f"连接状态: {source.check_connection()}")
    
    # 创建搜索请求
    request = MediaFetchRequest(
        subject_names=["测试动漫名称"],
        episode_sort=EpisodeSort(1)
    )
    
    # 执行搜索
    try:
        matches = list(source.fetch(request))
        logger.success(f"找到 {len(matches)} 个结果")
        for match in matches[:3]:
            logger.info(f"- {match.media.original_title}")
    except Exception as e:
        logger.error(f"测试失败: {e}")

if __name__ == "__main__":
    test_configuration()
