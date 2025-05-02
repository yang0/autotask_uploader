from typing import Dict, Any
import asyncio
import os
import json
from playwright.async_api import async_playwright

try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node


@register_node
class WeixinVideoUploaderNode(Node):
    NAME = "Weixin Video Uploader"
    DESCRIPTION = "Upload a video to WeChat Video Channel via Playwright automation."
    CATEGORY = "WeChat"
    VERSION = "1.0"

    INPUTS = {
        "video_path": {
            "label": "Video Path",
            "type": "STRING",
            "required": True,
            "description": "Path to the video file.",
            "widget": "FILE",
        },
        "title": {
            "label": "Title",
            "type": "STRING",
            "required": True,
            "description": "Video title.",
        },
        "description": {
            "label": "Description",
            "type": "STRING",
            "required": False,
            "default": "",
            "description": "Video description.",
        },
        "cookie_file": {
            "label": "Cookie File Path",
            "type": "STRING",
            "required": True,
            "description": "Path to the cookie file.",
            "widget": "FILE",
        },
        "is_original": {
            "label": "Is Original",
            "type": "BOOLEAN",
            "required": False,
            "default": True,
            "description": "Whether to declare as original content.",
        },
        "tags": {
            "label": "Tags",
            "type": "STRING",
            "required": False,
            "default": "",
            "description": "Tags for the video, separated by newlines.",
        },
    }

    OUTPUTS = {
        "success": {
            "label": "Success",
            "type": "BOOLEAN",
            "description": "Whether the upload was successful.",
        },
        "message": {
            "label": "Message",
            "type": "STRING",
            "description": "Result message or error info.",
        },
    }

    async def execute(
        self, node_inputs: Dict[str, Any], workflow_logger
    ) -> Dict[str, Any]:
        video_path = node_inputs.get("video_path")
        title = node_inputs.get("title")
        description = node_inputs.get("description", "")
        cookie_file = node_inputs.get("cookie_file")
        is_original = node_inputs.get("is_original", True)
        tags = node_inputs.get("tags", "")
        tag_list = [t.strip() for t in tags.split("\n") if t.strip()] if tags else []

        async def create_context_with_cookies(p, cookie_file):
            browser = await p.chromium.launch(headless=False)
            if cookie_file and os.path.exists(cookie_file):
                with open(cookie_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and ("cookies" in data or "origins" in data):
                    context = await browser.new_context(storage_state=cookie_file)
                elif isinstance(data, list):
                    context = await browser.new_context()
                    await context.add_cookies(data)
                else:
                    context = await browser.new_context()
            else:
                context = await browser.new_context()
            return context, browser

        try:
            async with async_playwright() as p:
                context, browser = await create_context_with_cookies(p, cookie_file)
                page = await context.new_page()
                await page.goto("https://channels.weixin.qq.com/platform/post/create")
                workflow_logger.info("Navigated to WeChat video upload page.")

                # 上传视频
                await page.wait_for_selector(
                    "div.ant-upload.ant-upload-drag", timeout=15000
                )
                file_input = await page.query_selector(
                    'input[type="file"][accept="video/mp4,video/x-m4v,video/*"]'
                )
                if not file_input:
                    return {"success": False, "message": "File input not found."}
                await file_input.set_input_files(video_path)
                workflow_logger.info("Video file selected.")

                # 等待视频处理完成
                await page.wait_for_selector(
                    "div.post-album-display-wrap", timeout=60000
                )
                workflow_logger.info("Video processed.")

                # 填写标题
                title_input = await page.wait_for_selector(
                    'input.weui-desktop-form__input[placeholder*="概括视频主要内容"]',
                    timeout=15000,
                )
                await title_input.click()
                await title_input.fill(title)
                workflow_logger.info("Title filled.")

                # 填写描述和标签
                full_description = description + (
                    "\n" + " ".join(tag_list) if tag_list else ""
                )
                desc_input = await page.wait_for_selector(
                    "div.post-desc-box div.input-editor", timeout=15000
                )
                await desc_input.click()
                await desc_input.fill(full_description)
                workflow_logger.info("Description and tags filled.")

                # 勾选原创声明
                if is_original:
                    checkbox = await page.wait_for_selector(
                        "div.declare-original-checkbox input[type='checkbox']",
                        timeout=15000,
                    )
                    await checkbox.check()
                    workflow_logger.info("Original content declaration checked.")
                    # 处理原创权益模态窗
                    try:
                        modal_title = await page.wait_for_selector(
                            'h3.weui-desktop-dialog__title:text("原创权益")',
                            timeout=15000,
                        )
                        modal = await modal_title.evaluate_handle(
                            'node => node.closest(".weui-desktop-dialog")'
                        )
                        # 勾选协议
                        proto_wrappers = await modal.query_selector_all(
                            "div.original-proto-wrapper"
                        )
                        proto_checkbox = None
                        for wrapper in proto_wrappers:
                            proto_text = await wrapper.inner_text()
                            if "我已阅读并同意" in proto_text:
                                proto_checkbox = await wrapper.query_selector(
                                    "input.ant-checkbox-input[type='checkbox']"
                                )
                                break
                        if not proto_checkbox:
                            return {
                                "success": False,
                                "message": "Agreement checkbox not found in modal.",
                            }
                        await proto_checkbox.check()
                        # 点击声明原创按钮
                        buttons = await modal.query_selector_all(
                            "button.weui-desktop-btn.weui-desktop-btn_primary"
                        )
                        found = False
                        for btn in buttons:
                            text = await btn.inner_text()
                            if "声明原创" in text:
                                await btn.click()
                                found = True
                                break
                        if not found:
                            return {
                                "success": False,
                                "message": "'声明原创' button not found in modal.",
                            }
                        await page.wait_for_selector(
                            'h3.weui-desktop-dialog__title:text("原创权益")',
                            state="hidden",
                            timeout=5000,
                        )
                        workflow_logger.info("Original content modal handled.")
                    except Exception as e:
                        workflow_logger.warning(
                            f"Original content modal handling failed: {e}"
                        )

                # 等待"删除"按钮出现，确保视频上传完成
                await page.wait_for_selector(
                    'div.finder-tag-wrap .tag-inner:text("删除")', timeout=120000
                )
                await asyncio.sleep(5)
                workflow_logger.info("Video upload confirmed by '删除' button.")

                # 点击"发表"按钮
                buttons = await page.query_selector_all(
                    "button.weui-desktop-btn.weui-desktop-btn_primary"
                )
                found = False
                for btn in buttons:
                    text = await btn.inner_text()
                    if "发表" in text:
                        await btn.click()
                        found = True
                        break
                if not found:
                    return {"success": False, "message": "'发表' button not found."}
                workflow_logger.info("Submit button (发表) clicked.")

                await asyncio.sleep(5)
                await context.close()
                await browser.close()
                return {
                    "success": True,
                    "message": "Video uploaded and submitted successfully.",
                }
        except Exception as e:
            workflow_logger.error(f"Weixin video upload failed: {e}")
            return {"success": False, "message": str(e)}
