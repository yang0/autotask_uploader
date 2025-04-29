# autotask_uploader

AutoTask 插件：小红书视频/图文自动上传节点

## 功能简介

本插件为 [AutoTask](https://github.com/yang0/autotask_core) 工作流系统提供小红书内容自动上传能力，支持：
- 小红书视频自动上传
- 小红书多图图文自动上传

## 节点说明

### 小红书视频上传节点
- **video_path**：视频文件路径（支持本地路径）
- **title**：视频标题
- **desc**：视频描述
- **cookie_file**：小红书已登录的cookie文件（支持 Playwright storage_state 格式）

### 小红书图文上传节点
- **pics**：图片文件路径列表（支持多图，空格或逗号分隔）
- **title**：图文标题
- **desc**：图文描述
- **cookie_file**：小红书已登录的cookie文件

## 典型应用场景
- 批量内容分发到小红书
- 自动化新媒体运营
- 跨平台内容同步

## 依赖
- [Playwright](https://playwright.dev/python/) (需提前安装并下载浏览器驱动)
- Python 3.8+

## 使用方法
1. 在 AutoTask 工作流中添加"小红书视频上传"或"小红书图文上传"节点。
2. 配置参数（视频/图片路径、标题、描述、cookie文件）。
3. 运行工作流，自动完成内容上传。

## 注意事项
- cookie 文件需为已登录小红书创作平台的 storage_state 格式或 cookies 数组。
- 建议使用稳定网络环境，避免因网络问题导致上传失败。
- Playwright 需提前安装并初始化浏览器驱动：
  ```bash
  pip install playwright
  playwright install
  ```

## License
MIT
