#!/usr/bin/env python3
"""
基于实际分析结果的 girigirilove 配置
使用发现的搜索表单格式
"""

import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web_scraper.core import SelectorMediaSource
from web_scraper.models import (
    SelectorSearchConfig, MediaFetchRequest, EpisodeSort,
    SelectorSubjectFormatConfig, SelectorChannelFormatConfig, MatchVideoConfig
)
from web_scraper.utils.logger import logger


def create_girigirilove_config():
    """
    基于实际分析创建的 girigirilove 配置
    
    发现的信息:
    - 搜索表单: GET /search/-------------/ 
    - 搜索字段: name='wd'
    - 特殊的URL结构，可能需要替换占位符
    """
    return SelectorSearchConfig(
        # 基于发现的搜索表单格式
        # 可能需要将 '-------------' 替换为实际的关键词
        search_url="https://anime.girigirilove.com/search/{keyword}/",
        
        # 搜索设置
        search_use_only_first_word=False,  # 保留完整关键词
        search_remove_special=True,        # 移除特殊字符，因为URL路径不支持特殊字符
        search_use_subject_names_count=1,  # 先测试单个名称
        
        # 请求设置
        request_interval_seconds=3.0,      # 较长间隔避免被屏蔽
        
        # 主题格式配置 - 需要根据实际搜索结果页面调整
        subject_format_config=SelectorSubjectFormatConfig(
            # 通用的可能选择器
            subject_selector=".anime-item, .search-item, .result-item, .show-item, .video-item, .card, li[class*='item']",
            name_selector=".title, .name, .anime-title, .show-title, h3, h4, .card-title, a[title]",
            url_selector="a, .link, .detail-link, .show-link"
        ),
        
        # 频道格式配置 - 剧集页面的结构
        channel_format_config=SelectorChannelFormatConfig(
            episode_selector=".episode, .ep-item, .playlist-item, .video-item, .play-item, li[class*='ep']",
            name_selector=".ep-title, .episode-title, .episode-name, .title, .name",
            url_selector="a, .play-btn, .episode-link, .watch-link"
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


def create_alternative_search_config():
    """
    备选配置 - 尝试不同的URL格式
    """
    config = create_girigirilove_config()
    
    # 尝试将占位符替换为参数格式
    config.search_url = "https://anime.girigirilove.com/search/?wd={keyword}"
    
    return config


class CustomGirigiriloveSource(SelectorMediaSource):
    """
    自定义的 girigirilove 数据源
    处理特殊的URL格式
    """
    
    def _process_search_url(self, keyword):
        """处理特殊的搜索URL格式"""
        # 基本的URL编码和处理
        processed_keyword = re.sub(r'[^\w\s-]', '', keyword)  # 移除特殊字符
        processed_keyword = processed_keyword.strip().replace(' ', '-')
        
        # 替换URL中的占位符
        if '-------------' in self.config.search_url:
            return self.config.search_url.replace('-------------', processed_keyword)
        else:
            return self.config.search_url.replace('{keyword}', processed_keyword)
    
    async def search(self, search_config, query):
        """覆盖搜索方法以处理特殊URL格式"""
        # 处理搜索URL
        original_url = search_config.search_url
        search_config.search_url = self._process_search_url(query.subject_name)
        
        logger.info(f"处理后的搜索URL: {search_config.search_url}")
        
        try:
            # 调用父类的搜索方法
            result = await super().search(search_config, query)
            return result
        finally:
            # 恢复原始URL
            search_config.search_url = original_url


def test_custom_source():
    """测试自定义数据源"""
    logger.info("=== 测试自定义 girigirilove 数据源 ===")
    
    config = create_girigirilove_config()
    source = CustomGirigiriloveSource("girigirilove-custom", config)
    
    # 测试连接
    connection_status = source.check_connection()
    logger.info(f"连接状态: {connection_status}")
    
    # 创建测试请求
    test_queries = [
        "进击的巨人",
        "鬼灭之刃",
        "海贼王"
    ]
    
    for query in test_queries:
        logger.info(f"\n测试搜索: {query}")
        
        # 测试URL处理
        processed_url = source._process_search_url(query)
        logger.info(f"处理后URL: {processed_url}")
        
        # 创建搜索请求
        request = MediaFetchRequest(
            subject_names=[query],
            episode_sort=EpisodeSort(1)
        )
        
        try:
            matches = list(source.fetch(request))
            
            if matches:
                logger.success(f"找到 {len(matches)} 个结果:")
                for i, match in enumerate(matches[:3]):
                    logger.info(f"  {i+1}. {match.media.original_title}")
                    logger.info(f"     URL: {match.media.download.url}")
            else:
                logger.warning(f"未找到 '{query}' 的搜索结果")
                
        except Exception as e:
            logger.error(f"搜索 '{query}' 时出错: {e}")
            
            # 如果是URL相关错误，尝试备选格式
            if "404" in str(e) or "500" in str(e):
                logger.info("尝试备选URL格式...")
                alt_config = create_alternative_search_config()
                alt_source = SelectorMediaSource("girigirilove-alt", alt_config)
                
                try:
                    alt_matches = list(alt_source.fetch(request))
                    if alt_matches:
                        logger.success(f"备选格式成功! 找到 {len(alt_matches)} 个结果")
                except Exception as alt_e:
                    logger.error(f"备选格式也失败: {alt_e}")


def manual_test_instructions():
    """提供手动测试说明"""
    logger.info("\n=== 手动测试说明 ===")
    
    instructions = [
        "由于网站可能使用特殊的URL结构，建议进行手动验证:",
        "",
        "1. 在浏览器中打开 https://anime.girigirilove.com/",
        "2. 在搜索框中输入 '进击的巨人'",
        "3. 提交搜索并观察页面跳转的URL",
        "4. 记录实际的搜索结果页面URL格式",
        "5. 查看搜索结果页面的HTML结构",
        "6. 根据实际URL和HTML结构修改配置",
        "",
        "可能需要修改的配置项:",
        "- search_url: 搜索URL的实际格式",
        "- subject_selector: 搜索结果项的容器选择器", 
        "- name_selector: 动漫标题的选择器",
        "- url_selector: 详情页链接的选择器"
    ]
    
    for instruction in instructions:
        if instruction == "":
            print()
        elif instruction.startswith("可能需要修改"):
            logger.warning(instruction)
        elif instruction.startswith(("1.", "2.", "3.", "4.", "5.", "6.")):
            logger.info(instruction)
        elif instruction.startswith("-"):
            logger.info(instruction)
        else:
            logger.info(instruction)


def main():
    """主函数"""
    logger.info("🎬 girigirilove 最终配置测试")
    logger.info("=" * 60)
    
    # 测试自定义数据源
    test_custom_source()
    
    # 提供手动测试说明
    manual_test_instructions()
    
    logger.info("\n" + "=" * 60)
    logger.success("配置测试完成！")
    logger.info("如果自动化测试失败，请按照手动测试说明进行验证。")


if __name__ == "__main__":
    main()