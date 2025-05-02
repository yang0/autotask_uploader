try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

from typing import Dict, Any
import asyncio
import json
import os
from playwright.async_api import async_playwright
import time

@register_node
class BaijiahaoVideoUploadNode(Node):
    NAME = "Baijiahao Video Upload"
    DESCRIPTION = "Upload a video to Baijiahao using Playwright automation."
    CATEGORY = "Baijiahao"

    INPUTS = {
        "video_path": {
            "label": "Video File Path",
            "description": "Path to the video file to upload.",
            "type": "STRING",
            "required": True,
            "widget": "FILE",
        },
        "title": {
            "label": "Video Title",
            "description": "Title of the video (max 30 characters).",
            "type": "STRING",
            "required": True,
        },
        "description": {
            "label": "Video Description",
            "description": "Description of the video.",
            "type": "STRING",
            "required": True,
        },
        "tags": {
            "label": "Tags",
            "description": "List of tags for the video (comma separated or JSON array).",
            "type": "STRING",
            "required": False,
        },
        "cookie_file": {
            "label": "Cookie File Path",
            "description": "Path to the Baijiahao cookies JSON file.",
            "type": "STRING",
            "required": True,
            "widget": "FILE",
        },
    }

    OUTPUTS = {
        "success": {
            "label": "Success",
            "description": "Whether the upload was successful.",
            "type": "BOOLEAN",
        },
        "message": {
            "label": "Message",
            "description": "Result message or error.",
            "type": "STRING",
        },
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        video_path = node_inputs["video_path"]
        title = node_inputs["title"]
        description = node_inputs["description"]
        tags = node_inputs.get("tags", "")
        cookie_file = node_inputs["cookie_file"]

        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = [t.strip() for t in tags.split(",") if t.strip()]

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context(storage_state=cookie_file)
                page = await context.new_page()

                workflow_logger.info("Navigating to Baijiahao video upload page...")
                await page.goto("https://baijiahao.baidu.com/builder/rc/edit?type=videoV2", timeout=60000)
                workflow_logger.info("已进入百家号视频发布页")

                # 上传视频
                file_input = await page.query_selector("div[class^='video-main-container'] input[type='file']")
                if not file_input:
                    raise Exception("未找到视频上传输入框")
                await file_input.set_input_files(video_path)
                workflow_logger.info("视频文件已选择")

                # 等待视频上传完成（检测"上传中"消失、"上传失败"未出现）
                for _ in range(120):
                    uploading = await page.locator('div .cover-overlay:has-text("上传中")').count()
                    failed = await page.locator('div .cover-overlay:has-text("上传失败")').count()
                    if failed:
                        raise Exception("视频上传失败")
                    if not uploading:
                        workflow_logger.info("视频上传完毕")
                        break
                    await asyncio.sleep(2)
                else:
                    raise Exception("视频上传超时")

                # 滚动到页面底部，确保标题输入框渲染出来
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)

                # 填写标题
                await page.wait_for_selector("input[placeholder='添加标题获得更多推荐']", timeout=15000)
                title_input = await page.query_selector("input[placeholder='添加标题获得更多推荐']")
                await title_input.fill(title[:30])
                workflow_logger.info("标题已填写")

                # 填写简介
                await page.wait_for_selector("textarea[placeholder='让别人更懂你']", timeout=15000)
                desc_input = await page.query_selector("textarea[placeholder='让别人更懂你']")
                await desc_input.fill(description)
                workflow_logger.info("简介已填写")

                # 填写标签
                if tags:
                    tag_input = await page.wait_for_selector("input.cheetah-ui-pro-tag-input-container-tag-input[placeholder='获得精准推荐']", timeout=10000)
                    for tag in tags:
                        await tag_input.fill(tag)
                        await tag_input.press('Enter')
                        await asyncio.sleep(0.5)
                    workflow_logger.info("标签已填写")

                # 等待封面生成
                for _ in range(60):
                    if await page.locator("div.cheetah-spin-container img").count():
                        workflow_logger.info("封面已生成")
                        break
                    await asyncio.sleep(2)
                else:
                    workflow_logger.info("封面生成超时，继续尝试发布")

                # 找到所有包含"发布"文案的 op-btn-outter-content
                publish_btns = await page.query_selector_all("div.op-btn-outter-content")
                found = False
                for btn_wrap in publish_btns:
                    text = await btn_wrap.inner_text()
                    if "发布" in text:
                        # 找到对应的 button
                        btn = await btn_wrap.query_selector("button")
                        if btn:
                            await btn.click()
                            workflow_logger.info("已点击发布按钮")
                            found = True
                            break
                if not found:
                    raise Exception("未找到发布按钮")

                # 等待跳转或成功提示
                await asyncio.sleep(5)
                
                await context.close()
                await browser.close()

                return {
                    "success": True,
                    "message": "Video upload process completed. Please verify on Baijiahao."
                }

        except Exception as e:
            workflow_logger.error(f"Baijiahao upload failed: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }
