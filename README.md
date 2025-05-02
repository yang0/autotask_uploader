# autotask_uploader

AutoTask 插件：多平台视频/图文自动上传节点

## 功能简介

本插件为 [AutoTask](https://github.com/yang0/autotask_core) 工作流系统提供多平台内容自动上传能力，支持：
- 小红书视频和图文自动上传
- 抖音视频自动上传
- B站视频自动上传
- 百家号视频自动上传
- YouTube视频自动上传
- 快手视频自动上传
- 微信视频自动上传

## 节点说明

### 小红书视频上传节点
- **video_path**：视频文件路径（支持本地路径）
- **title**：视频标题
- **desc**：视频描述
- **cookie_file**：通过 AutoTask 登录管理获取的 cookie 文件路径

### 小红书图文上传节点
- **pics**：图片文件路径列表（支持多图，空格或逗号分隔）
- **title**：图文标题
- **desc**：图文描述
- **cookie_file**：通过 AutoTask 登录管理获取的 cookie 文件路径

### 抖音视频上传节点
- **video_path**：视频文件路径（支持本地路径）
- **title**：视频标题
- **description**：视频描述
- **tags**：视频标签（可选，支持字符串列表或逗号分隔的字符串）
- **cookie_file**：通过 AutoTask 登录管理获取的 cookie 文件路径

### B站视频上传节点
- **video_path**：视频文件路径
- **title**：视频标题
- **description**：视频简介
- **cookie_file**：通过 AutoTask 登录管理获取的 cookie 文件路径

### 百家号视频上传节点
- **video_path**：视频文件路径
- **title**：视频标题
- **description**：视频描述
- **cookie_file**：通过 AutoTask 登录管理获取的 cookie 文件路径

### YouTube视频上传节点
- **video_path**：视频文件路径
- **title**：视频标题
- **description**：视频描述
- **cookie_file**：通过 AutoTask 登录管理获取的 cookie 文件路径

### 快手视频上传节点
- **video_path**：视频文件路径
- **title**：视频标题
- **description**：视频描述
- **cookie_file**：通过 AutoTask 登录管理获取的 cookie 文件路径

### 微信视频上传节点
- **video_path**：视频文件路径
- **title**：视频标题
- **description**：视频描述
- **cookie_file**：通过 AutoTask 登录管理获取的 cookie 文件路径

## 典型应用场景
- 批量内容分发到各大平台
- 自动化新媒体运营
- 跨平台内容同步
- 多账号内容发布
- 定时发布管理

## 使用方法
1. 在 AutoTask 工作流中添加需要的平台上传节点
2. 通过 AutoTask 的登录管理功能获取目标平台的 cookie
3. 配置必要参数（视频/图片路径、标题、描述、cookie文件等）
4. 运行工作流，自动完成内容上传

## Cookie 获取说明
1. 打开 AutoTask 的登录管理界面
2. 选择需要登录的目标平台（如：抖音、小红书等）
3. 按照提示完成登录操作
4. 保存登录状态，并生成对应的 cookie 文件
5. 在上传节点中使用生成的 cookie 文件路径即可

## 注意事项
- cookie 文件会自动通过 AutoTask 的登录管理功能维护，无需手动处理
- 建议使用稳定网络环境，避免因网络问题导致上传失败


## License
MIT
