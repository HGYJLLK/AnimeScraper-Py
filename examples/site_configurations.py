#!/usr/bin/env python3
"""
网站配置示例 - 为常见动漫网站提供配置模板

这个文件展示了如何为不同类型的网站配置爬虫参数。
你可以复制这些模板并根据你的目标网站进行修改。
"""

from web_scraper.models import (
    SelectorSearchConfig, SelectorSubjectFormatConfig, 
    SelectorChannelFormatConfig, MatchVideoConfig
)
from web_scraper.utils.logger import logger


def create_generic_anime_site_config():
    """
    通用动漫网站配置模板
    适用于大多数标准结构的动漫网站
    """
    return SelectorSearchConfig(
        # 搜索设置
        search_url="https://你的网站.com/search?keyword={keyword}",
        search_use_only_first_word=True,  # 只使用第一个关键词搜索
        search_remove_special=True,       # 移除特殊字符
        search_use_subject_names_count=2, # 使用前两个主题名称搜索
        
        # 请求设置
        request_interval_seconds=2.0,     # 请求间隔2秒
        only_supports_players=None,       # 支持所有播放器
        
        # 主题格式配置（搜索结果页面）
        subject_format_config=SelectorSubjectFormatConfig(
            subject_selector=".search-result-item",  # 搜索结果项的选择器
            name_selector=".anime-title",            # 动漫标题选择器
            url_selector="a.anime-link"              # 动漫链接选择器
        ),
        
        # 频道格式配置（剧集列表页面）
        channel_format_config=SelectorChannelFormatConfig(
            episode_selector=".episode-item",       # 剧集项选择器
            name_selector=".episode-title",         # 剧集标题选择器
            url_selector="a.episode-link",          # 剧集链接选择器
            channel_selector=".quality-badge"      # 画质/频道选择器（可选）
        ),
        
        # 视频匹配配置
        match_video=MatchVideoConfig(
            enable_nested_url=True,
            match_video_url=r"(\.mp4|\.m3u8|video\.php)",  # 匹配视频URL的正则
            cookies="",                              # 如果需要cookies
        ),
        
        # 默认设置
        default_resolution="1080P",
        default_subtitle_language="CHS"
    )


def create_simple_list_site_config():
    """
    简单列表型网站配置
    适用于直接显示剧集列表的网站
    """
    return SelectorSearchConfig(
        search_url="https://简单网站.com/anime/{keyword}",
        
        subject_format_config=SelectorSubjectFormatConfig(
            subject_selector=".anime-card",
            name_selector="h3.title",
            url_selector="a"
        ),
        
        # 使用无频道格式
        channel_format_id="channel_format_no_channel",
        channel_format_config=SelectorChannelFormatConfig(
            episode_selector=".ep-list li",
            name_selector=".ep-name",
            url_selector=".ep-link"
        ),
        
        request_interval_seconds=1.5,
        default_resolution="720P"
    )


def create_grouped_episodes_site_config():
    """
    分组剧集网站配置
    适用于按画质或来源分组显示剧集的网站
    """
    return SelectorSearchConfig(
        search_url="https://分组网站.com/search/{keyword}",
        
        subject_format_config=SelectorSubjectFormatConfig(
            subject_selector=".result-item",
            name_selector=".show-title",
            url_selector=".detail-link"
        ),
        
        # 使用分组频道格式
        channel_format_id="channel_format_index_grouped", 
        channel_format_config=SelectorChannelFormatConfig(
            episode_selector=".episode-group .ep-item",
            name_selector=".ep-title",
            url_selector=".play-btn",
            channel_selector=".quality-tag"  # 获取画质信息
        ),
        
        request_interval_seconds=3.0,
        default_resolution="1080P"
    )


def create_ajax_api_site_config():
    """
    AJAX API 类型网站配置
    适用于使用API接口的现代网站
    """
    return SelectorSearchConfig(
        search_url="https://api网站.com/api/search?q={keyword}&format=json",
        
        # 可能需要特殊的选择器来处理JSON响应
        subject_format_config=SelectorSubjectFormatConfig(
            subject_selector=".data-item",  # 如果API返回HTML包装的数据
            name_selector=".title",
            url_selector=".link"
        ),
        
        channel_format_config=SelectorChannelFormatConfig(
            episode_selector=".playlist-item",
            name_selector=".episode-name", 
            url_selector=".play-url"
        ),
        
        # API通常需要更少的延迟
        request_interval_seconds=0.5,
        
        # 可能需要特殊的视频URL匹配
        match_video=MatchVideoConfig(
            enable_nested_url=True,
            match_video_url=r"(stream\.php|play\.m3u8|\.mp4)",
            cookies="session_id=xxx; user_pref=hd"
        )
    )


def demonstrate_configuration_usage():
    """演示如何使用配置"""
    logger.info("=== 网站配置示例 ===")
    
    # 1. 通用配置
    generic_config = create_generic_anime_site_config()
    logger.info(f"通用配置搜索URL: {generic_config.search_url}")
    logger.info(f"主题选择器: {generic_config.subject_format_config.subject_selector}")
    
    # 2. 简单列表配置
    simple_config = create_simple_list_site_config()
    logger.info(f"简单配置剧集选择器: {simple_config.channel_format_config.episode_selector}")
    
    # 3. 分组配置
    grouped_config = create_grouped_episodes_site_config()
    logger.info(f"分组配置频道选择器: {grouped_config.channel_format_config.channel_selector}")
    
    logger.success("配置示例创建完成！")
    logger.info("使用步骤：")
    logger.info("1. 选择最适合你目标网站的配置模板")
    logger.info("2. 修改URL和CSS选择器")
    logger.info("3. 使用浏览器开发者工具找到正确的选择器")
    logger.info("4. 测试配置是否工作正常")


def get_css_selector_tips():
    """获取CSS选择器使用技巧"""
    tips = [
        "使用浏览器开发者工具 (F12) 来查找元素",
        "右键点击元素 → 检查元素 → 复制选择器",
        "常用选择器模式:",
        "  .class-name      - 按class选择",
        "  #element-id      - 按ID选择", 
        "  tag.class        - 标签+class组合",
        "  .parent .child   - 嵌套选择",
        "  [attribute='value'] - 按属性选择",
        "测试选择器: 在浏览器控制台使用 document.querySelectorAll('选择器')",
        "优先使用稳定的class名称，避免使用数字编号的class"
    ]
    
    logger.info("=== CSS选择器使用技巧 ===")
    for tip in tips:
        logger.info(tip)
    
    return tips


if __name__ == "__main__":
    # 演示配置使用
    demonstrate_configuration_usage()
    
    # 显示CSS选择器技巧
    print()  # 空行分隔
    get_css_selector_tips()
    
    logger.success("查看配置示例完成！下一步可以开始自定义配置。")