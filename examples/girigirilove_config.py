#!/usr/bin/env python3
"""
girigirilove 动漫网站配置
网站: https://anime.girigirilove.com/

基于网站分析创建的配置，可能需要根据实际测试结果进行调整。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web_scraper.core import SelectorMediaSource
from web_scraper.models import (
    SelectorSearchConfig, MediaFetchRequest, EpisodeSort,
    SelectorSubjectFormatConfig, SelectorChannelFormatConfig, MatchVideoConfig
)
from web_scraper.utils.logger import logger


def create_girigirilove_config():
    """创建 girigirilove 网站配置"""
    return SelectorSearchConfig(
        # 搜索URL - 基于网站分析，可能的搜索格式
        search_url="https://anime.girigirilove.com/search/{keyword}/",
        
        # 搜索设置
        search_use_only_first_word=False,  # 保留完整搜索词
        search_remove_special=True,        # 移除特殊字符
        search_use_subject_names_count=2,  # 尝试多个名称
        
        # 请求设置 - 适度的请求间隔
        request_interval_seconds=3.0,      # 3秒间隔，避免被屏蔽
        
        # 主题格式配置（搜索结果页面）
        # 这些选择器需要根据实际HTML调整
        subject_format_config=SelectorSubjectFormatConfig(
            # 可能的动漫卡片容器选择器
            subject_selector=".anime-item, .card-item, .list-item, .search-result",
            # 可能的标题选择器
            name_selector=".title, .anime-title, .name, h3, h4, .card-title",
            # 可能的链接选择器
            url_selector="a, .link, .detail-link"
        ),
        
        # 频道格式配置（剧集列表页面）
        channel_format_config=SelectorChannelFormatConfig(
            # 可能的剧集容器选择器
            episode_selector=".episode, .ep-item, .playlist-item, .video-item",
            # 可能的剧集名称选择器
            name_selector=".ep-title, .episode-name, .title, .name",
            # 可能的播放链接选择器
            url_selector="a, .play-btn, .episode-link, .watch-link"
        ),
        
        # 视频匹配配置
        match_video=MatchVideoConfig(
            enable_nested_url=True,
            # 匹配常见视频URL模式
            match_video_url=r"(\.mp4|\.m3u8|/play/|/video/|stream)",
            cookies="",  # 如果需要可以添加cookies
        ),
        
        # 默认设置
        default_resolution="1080P",
        default_subtitle_language="CHS"
    )


def create_alternative_config():
    """创建备选配置 - 不同的搜索URL格式"""
    config = create_girigirilove_config()
    # 尝试不同的搜索URL格式
    config.search_url = "https://anime.girigirilove.com/search?keyword={keyword}"
    return config


def create_api_style_config():
    """创建API风格的配置 - 如果网站使用AJAX加载"""
    config = create_girigirilove_config()
    config.search_url = "https://anime.girigirilove.com/api/search?q={keyword}"
    return config


def test_connection():
    """测试网站连接"""
    logger.info("=== 测试 girigirilove 网站连接 ===")
    
    configs = [
        ("主要配置", create_girigirilove_config()),
        ("备选配置", create_alternative_config()),
        ("API配置", create_api_style_config())
    ]
    
    for config_name, config in configs:
        logger.info(f"\n测试 {config_name}:")
        logger.info(f"搜索URL: {config.search_url}")
        
        source = SelectorMediaSource("girigirilove", config)
        
        # 测试基本连接
        connection_status = source.check_connection()
        logger.info(f"连接状态: {connection_status}")
        
        if connection_status == "SUCCESS":
            logger.success(f"{config_name} 连接成功！")
            return config, source
        else:
            logger.warning(f"{config_name} 连接失败")
    
    logger.error("所有配置都无法连接，可能需要进一步调试")
    return None, None


def test_search():
    """测试搜索功能"""
    logger.info("\n=== 测试搜索功能 ===")
    
    config, source = test_connection()
    if not source:
        logger.error("无法建立连接，跳过搜索测试")
        return
    
    # 创建搜索请求
    test_queries = [
        "进击的巨人",
        "鬼灭之刃", 
        "attack on titan"
    ]
    
    for query in test_queries:
        logger.info(f"\n搜索: {query}")
        
        request = MediaFetchRequest(
            subject_names=[query],
            episode_sort=EpisodeSort(1)
        )
        
        try:
            # 执行搜索
            matches = list(source.fetch(request))
            
            if matches:
                logger.success(f"找到 {len(matches)} 个结果:")
                for i, match in enumerate(matches[:3]):  # 显示前3个
                    logger.info(f"  {i+1}. {match.media.original_title}")
                    logger.info(f"     URL: {match.media.download.url}")
                break  # 找到结果就停止
            else:
                logger.warning(f"未找到 '{query}' 的搜索结果")
                
        except Exception as e:
            logger.error(f"搜索 '{query}' 时出错: {e}")
            # 继续测试下一个查询
    
    logger.info("\n搜索测试完成")


def debug_selectors():
    """调试选择器 - 提供手动调试建议"""
    logger.info("\n=== 选择器调试建议 ===")
    
    debug_steps = [
        "1. 手动访问网站: https://anime.girigirilove.com/",
        "2. 尝试搜索一个动漫（比如'进击的巨人'）",
        "3. 观察搜索结果页面的URL格式",
        "4. 使用F12开发者工具查看搜索结果的HTML结构",
        "5. 找到以下元素的CSS选择器:",
        "   - 每个搜索结果的容器元素",
        "   - 动漫标题元素", 
        "   - 动漫详情页链接",
        "6. 进入一个动漫详情页，查看剧集列表的结构",
        "7. 修改本文件中的选择器配置",
        "8. 重新运行测试"
    ]
    
    for step in debug_steps:
        if step.startswith(("1.", "2.", "3.", "4.", "6.", "8.")):
            logger.info(step)
        elif step.startswith("5."):
            logger.warning(step)
        else:
            logger.info(step)
    
    logger.info("\n如果网站使用JavaScript动态加载内容，")
    logger.info("可能需要使用Selenium等工具或寻找API接口。")


def main():
    """主函数"""
    logger.info("🎬 girigirilove 动漫网站爬虫配置")
    logger.info("=" * 50)
    
    # 测试连接
    test_connection()
    
    # 测试搜索（如果连接成功）
    test_search()
    
    # 提供调试建议
    debug_selectors()
    
    logger.info("\n" + "=" * 50)
    logger.success("配置测试完成！")
    logger.info("下一步：根据实际测试结果调整选择器配置")


if __name__ == "__main__":
    main()