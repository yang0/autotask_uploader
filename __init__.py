from .xhs_uploader import *
from .bilibili_uploader import *
from .baijiahao_uploader import *
from .youtube_uploader import *
from .kuaishou_uploader import *
from .douyin_uploader import *
from .weixin_uploader import *

VERSION = "1.0.0"
GIT_URL = "https://github.com/yourname/autotask_uploader.git"
NAME = "AutoTask Uploader"
DESCRIPTION = """提供多平台视频和图文自动上传的工作流节点。

• 工作流节点
  - 小红书视频上传：自动化上传视频到小红书创作平台
  - 小红书图文上传：自动化上传多图图文到小红书创作平台
  - 抖音视频上传：自动化上传视频到抖音创作者平台
  - B站视频上传：自动化上传视频到B站创作中心
  - 百家号视频上传：自动化上传视频到百家号
  - YouTube视频上传：自动化上传视频到YouTube
  - 快手视频上传：自动化上传视频到快手创作者平台
  - 微信视频上传：自动化上传视频到微信公众平台

• 典型应用场景
  - 批量内容分发
  - 自动化新媒体运营
  - 跨平台内容同步
  - 多账号内容发布

本插件依赖 Playwright 实现浏览器自动化。
"""
TAGS = ["小红书", "抖音", "B站", "YouTube", "微信"]
