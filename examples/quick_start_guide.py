#!/usr/bin/env python3
"""
快速开始指南 - 如何为你的目标网站配置爬虫

这个指南将逐步教你如何：
1. 分析目标网站结构
2. 配置CSS选择器
3. 测试和调试配置
4. 运行完整的爬虫
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web_scraper.core import SelectorMediaSource
from web_scraper.models import (
    SelectorSearchConfig, MediaFetchRequest, EpisodeSort,
    SelectorSubjectFormatConfig, SelectorChannelFormatConfig, MatchVideoConfig
)
from web_scraper.utils.logger import logger


class QuickStartGuide:
    """快速开始指南类"""
    
    def __init__(self):
        self.step = 1
    
    def print_step(self, title, description):
        """打印步骤信息"""
        logger.info(f"=== 步骤 {self.step}: {title} ===")
        logger.info(description)
        self.step += 1
        print()  # 空行
    
    def step1_analyze_website(self):
        """步骤1: 分析网站结构"""
        self.print_step(
            "分析目标网站结构",
            "首先，你需要分析目标动漫网站的页面结构："
        )
        
        analysis_steps = [
            "1. 打开目标网站的搜索页面",
            "2. 搜索一个动漫（比如 '进击的巨人'）",
            "3. 观察搜索结果页面的HTML结构：",
            "   - 每个搜索结果的容器元素",
            "   - 动漫标题的位置", 
            "   - 动漫详情页链接的位置",
            "4. 点击进入一个动漫的详情页",
            "5. 观察剧集列表页面的HTML结构：",
            "   - 每个剧集的容器元素",
            "   - 剧集标题的位置",
            "   - 剧集播放链接的位置",
            "   - 是否有画质/来源分组"
        ]
        
        for step in analysis_steps:
            logger.info(step)
    
    def step2_create_config(self):
        """步骤2: 创建配置"""
        self.print_step(
            "创建网站配置",
            "基于分析结果创建配置文件："
        )
        
        # 示例配置代码
        example_config = '''
# 创建配置示例
config = SelectorSearchConfig(
    # 搜索URL - 用 {keyword} 作为关键词占位符
    search_url="https://your-anime-site.com/search?q={keyword}",
    
    # 主题格式配置（搜索结果页面）
    subject_format_config=SelectorSubjectFormatConfig(
        subject_selector=".search-item",    # 每个搜索结果的容器
        name_selector=".anime-title",       # 动漫标题元素
        url_selector="a.detail-link"        # 详情页链接元素
    ),
    
    # 频道格式配置（剧集列表页面）  
    channel_format_config=SelectorChannelFormatConfig(
        episode_selector=".episode-item",   # 每个剧集的容器
        name_selector=".ep-title",          # 剧集标题元素
        url_selector=".play-link"           # 播放链接元素
    ),
    
    # 其他设置
    request_interval_seconds=2.0,           # 请求间隔
    default_resolution="1080P",
    default_subtitle_language="CHS"
)
'''
        logger.info("配置文件模板：")
        print(example_config)
    
    def step3_find_selectors(self):
        """步骤3: 查找CSS选择器"""
        self.print_step(
            "查找正确的CSS选择器",
            "使用浏览器开发者工具找到正确的选择器："
        )
        
        selector_steps = [
            "1. 在网站上按F12打开开发者工具",
            "2. 使用元素选择工具（点击左上角箭头图标）",
            "3. 点击你想选择的元素（比如动漫标题）",
            "4. 在开发者工具中会高亮显示对应的HTML元素",
            "5. 右键点击HTML元素 → Copy → Copy selector",
            "6. 粘贴到配置文件中对应的位置",
            "7. 在控制台中测试选择器：",
            "   document.querySelectorAll('你的选择器')",
            "8. 确保选择器能选中所有需要的元素"
        ]
        
        for step in selector_steps:
            logger.info(step)
        
        logger.warning("注意事项：")
        logger.warning("- 选择器要尽可能稳定，避免使用随机生成的class名")
        logger.warning("- 测试多个页面确保选择器通用性")
        logger.warning("- 优先使用语义化的class名称")
    
    def step4_test_config(self):
        """步骤4: 测试配置"""
        self.print_step(
            "测试配置是否正确",
            "创建测试脚本验证配置："
        )
        
        test_code = '''
# 测试配置示例
from web_scraper.core import SelectorMediaSource
from web_scraper.models import MediaFetchRequest, EpisodeSort

# 使用你的配置创建媒体源
source = SelectorMediaSource("test-site", your_config)

# 测试连接
connection_status = source.check_connection()
logger.info(f"连接状态: {connection_status}")

# 创建搜索请求
request = MediaFetchRequest(
    subject_names=["进击的巨人", "Attack on Titan"],
    episode_sort=EpisodeSort(1)
)

# 执行搜索（这会实际访问网站）
try:
    matches = list(source.fetch(request))
    logger.success(f"找到 {len(matches)} 个匹配结果")
    
    for i, match in enumerate(matches[:3]):
        logger.info(f"  {i+1}. {match.media.original_title}")
        logger.info(f"     URL: {match.media.download.url}")
        
except Exception as e:
    logger.error(f"测试失败: {e}")
    logger.info("请检查CSS选择器是否正确")
'''
        
        logger.info("测试代码模板：")
        print(test_code)
    
    def step5_debug_tips(self):
        """步骤5: 调试技巧"""
        self.print_step(
            "常见问题和调试技巧",
            "遇到问题时的调试方法："
        )
        
        debug_tips = [
            "问题：找不到搜索结果",
            "  - 检查搜索URL是否正确",
            "  - 确认subject_selector能选中搜索结果",
            "  - 使用浏览器验证URL和选择器",
            "",
            "问题：找不到剧集",
            "  - 检查episode_selector是否正确",
            "  - 确认详情页URL能正常访问",
            "  - 检查是否需要特殊的请求头",
            "",
            "问题：选择器不工作",
            "  - 在浏览器控制台测试选择器",
            "  - 检查页面是否使用JavaScript动态加载内容",
            "  - 尝试更简单的选择器",
            "",
            "问题：被网站屏蔽",
            "  - 增加request_interval_seconds",
            "  - 添加合适的User-Agent",
            "  - 考虑使用代理"
        ]
        
        for tip in debug_tips:
            if tip.startswith("问题："):
                logger.warning(tip)
            elif tip == "":
                print()
            else:
                logger.info(tip)


def create_template_file():
    """创建配置模板文件"""
    template_content = '''#!/usr/bin/env python3
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
'''
    
    template_path = os.path.join(os.path.dirname(__file__), "my_site_config.py")
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    logger.success(f"配置模板已创建: {template_path}")
    logger.info("你可以编辑这个文件来配置你的网站")


def main():
    """主函数"""
    logger.info("🎯 动漫爬虫快速开始指南")
    logger.info("=" * 50)
    
    guide = QuickStartGuide()
    
    # 运行指南步骤
    guide.step1_analyze_website()
    guide.step2_create_config()
    guide.step3_find_selectors()
    guide.step4_test_config()
    guide.step5_debug_tips()
    
    # 创建模板文件
    create_template_file()
    
    logger.success("快速开始指南完成！")
    logger.info("下一步：")
    logger.info("1. 编辑 my_site_config.py 文件")
    logger.info("2. 运行 python my_site_config.py 测试配置")
    logger.info("3. 根据测试结果调整选择器")


if __name__ == "__main__":
    main()