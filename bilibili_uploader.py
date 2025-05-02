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
class BilibiliVideoUploadNode(Node):
    NAME = "Bilibili Video Upload"
    DESCRIPTION = "Upload a video to Bilibili using Playwright automation."
    CATEGORY = "Bilibili"

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
            "description": "Title of the video.",
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
            "required": True,
        },
        "cookie_file": {
            "label": "Cookie File Path",
            "description": "Path to the Bilibili cookies JSON file.",
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
        tags = node_inputs["tags"]
        cookie_file = node_inputs["cookie_file"]
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = [t.strip() for t in tags.split(",") if t.strip()]
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await self._create_context_with_cookies(p, browser, cookie_file)
                page = await context.new_page()
                await page.goto("https://member.bilibili.com/platform/home")
                await page.wait_for_selector("#nav_upload_btn", timeout=15000)
                await page.click("#nav_upload_btn")
                upload_btn = await page.wait_for_selector("div.upload-btn", timeout=15000)
                await page.evaluate("el => { el.scrollIntoView({behavior: 'auto', block: 'center'}); el.focus(); el.click(); }", upload_btn)
                inputs = await page.query_selector_all("input[type='file']")
                found = False
                for inp in inputs:
                    try:
                        await inp.set_input_files(video_path)
                        await page.evaluate("el => el.dispatchEvent(new Event('change', { bubbles: true }))", inp)
                        found = True
                        break
                    except Exception:
                        continue
                if not found:
                    return {"success": False, "message": "No usable file input found."}
                await asyncio.sleep(5)
                for _ in range(6):
                    closed = False
                    try:
                        await page.wait_for_selector("button:has-text('暂不设置')", timeout=1000)
                        await page.click("button:has-text('暂不设置')")
                        closed = True
                    except Exception:
                        try:
                            await page.wait_for_selector("span:has-text('暂不设置')", timeout=500)
                            await page.click("span:has-text('暂不设置')")
                            closed = True
                        except Exception:
                            pass
                    if closed:
                        break
                    await asyncio.sleep(1)
                for _ in range(10):
                    close_btns = await page.query_selector_all(
                        ".input-container .tag-pre-wrp .close.icon-sprite.icon-sprite-off"
                    )
                    if not close_btns:
                        break
                    for btn in close_btns:
                        try:
                            if await btn.is_visible():
                                await btn.click()
                                await asyncio.sleep(0.3)
                        except Exception:
                            pass
                    await asyncio.sleep(0.3)
                for tag in tags:
                    await page.wait_for_selector("input[placeholder*='标签']", timeout=10000)
                    await page.fill("input[placeholder*='标签']", tag)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(0.5)
                await page.wait_for_selector("input[placeholder*='标题']", timeout=10000)
                await page.fill("input[placeholder*='标题']", title)
                await page.wait_for_selector("div.ql-editor", timeout=10000)
                for _ in range(5):
                    await page.click("div.ql-editor")
                    await page.fill("div.ql-editor", description)
                await page.wait_for_selector("span:has-text('立即投稿')", timeout=10000)
                await page.click("span:has-text('立即投稿')")
                await asyncio.sleep(2)
                await context.close()
                await browser.close()
                return {"success": True, "message": "Video upload process completed. Please verify on Bilibili."}
        except Exception as e:
            workflow_logger.error(f"Bilibili upload failed: {str(e)}")
            return {"success": False, "message": str(e)}

    async def _create_context_with_cookies(self, p, browser, cookie_file):
        if cookie_file and os.path.exists(cookie_file):
            with open(cookie_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and ('cookies' in data or 'origins' in data):
                context = await browser.new_context(storage_state=cookie_file)
            elif isinstance(data, list):
                context = await browser.new_context()
                await context.add_cookies(data)
            else:
                context = await browser.new_context()
        else:
            context = await browser.new_context()
        return context
