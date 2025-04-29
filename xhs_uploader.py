from autotask.nodes import Node, register_node
from typing import Dict, Any
import asyncio
import json
import os
from playwright.async_api import async_playwright
import traceback

@register_node
class XHSVideoUploaderNode(Node):
    NAME = "小红书视频上传"
    DESCRIPTION = "自动上传小红书视频"

    INPUTS = {
        "video_path": {
            "label": "视频文件路径",
            "type": "STRING",
            "required": True,
            "widget": "FILE"
        },
        "title": {
            "label": "标题",
            "type": "STRING",
            "required": True
        },
        "desc": {
            "label": "描述",
            "type": "STRING",
            "required": True
        },
        "cookie_file": {
            "label": "Cookie文件路径",
            "type": "STRING",
            "required": True,
            "widget": "FILE"
        }
    }

    OUTPUTS = {
        "success": {
            "label": "是否成功",
            "type": "BOOLEAN"
        },
        "error_message": {
            "label": "错误信息",
            "type": "STRING"
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        video_path = node_inputs["video_path"]
        title = node_inputs["title"]
        desc = node_inputs["desc"]
        cookie_file = node_inputs["cookie_file"]

        async def create_context_with_cookies(p, cookie_file):
            browser = await p.chromium.launch(headless=False)
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
            return context, browser

        try:
            async with async_playwright() as p:
                context, browser = await create_context_with_cookies(p, cookie_file)
                page = await context.new_page()
                # 最大化窗口
                try:
                    await page.evaluate("window.moveTo(0,0); window.resizeTo(screen.width, screen.height);")
                except Exception:
                    pass
                await page.goto(
                    "https://creator.xiaohongshu.com/publish/publish?source=official",
                    wait_until="domcontentloaded",
                    timeout=60000
                )
                # 进入视频tab
                try:
                    await page.get_by_text("上传视频", exact=True).click()
                except Exception:
                    traceback.print_exc()
                    pass

                await page.wait_for_selector('input.upload-input', timeout=15000)
                # 只选视频input
                inputs = await page.query_selector_all('input.upload-input')
                found = False
                for inp in inputs:
                    accept = await inp.get_attribute('accept')
                    if accept and ('.mp4' in accept or '.mov' in accept or 'video' in accept):
                        await inp.set_input_files(video_path)
                        found = True
                        break
                if not found:
                    return {"success": False, "error_message": "未找到支持视频的上传 input"}

                await asyncio.sleep(5)
                await page.wait_for_selector("input.d-text", timeout=10000)
                await page.fill("input.d-text", title)
                await page.wait_for_selector("div.ql-editor", timeout=10000)
                await page.click("div.ql-editor")
                await page.evaluate(
                    """(desc) => {
                        const editor = document.querySelector('div.ql-editor');
                        if (editor) {
                            editor.innerText = desc;
                        }
                    }""",
                    desc
                )
                try:
                    await page.wait_for_selector('button.publishBtn', timeout=10000)
                    await page.click('button.publishBtn')
                except Exception as e:
                    return {"success": False, "error_message": f"未能自动点击发布按钮: {e}"}
                await asyncio.sleep(5)
                await context.close()
                await browser.close()
            return {"success": True, "error_message": ""}
        except Exception as e:
            return {"success": False, "error_message": str(e)}

@register_node
class XHSPicsUploaderNode(Node):
    NAME = "小红书图文上传"
    DESCRIPTION = "自动上传小红书图文（多图）"

    INPUTS = {
        "pics": {
            "label": "图片文件路径列表",
            "type": "STRING",
            "required": True,
            "widget": "FILE"
        },
        "title": {
            "label": "标题",
            "type": "STRING",
            "required": True
        },
        "desc": {
            "label": "描述",
            "type": "STRING",
            "required": True
        },
        "cookie_file": {
            "label": "Cookie文件路径",
            "type": "STRING",
            "required": True,
            "widget": "FILE"
        }
    }

    OUTPUTS = {
        "success": {
            "label": "是否成功",
            "type": "BOOLEAN"
        },
        "error_message": {
            "label": "错误信息",
            "type": "STRING"
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        pics = node_inputs["pics"]
        if isinstance(pics, str):
            # 支持逗号或空格分隔
            pics = [p.strip() for p in pics.replace(',', ' ').split() if p.strip()]
        title = node_inputs["title"]
        desc = node_inputs["desc"]
        cookie_file = node_inputs["cookie_file"]

        async def create_context_with_cookies(p, cookie_file):
            browser = await p.chromium.launch(headless=True)
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
            return context, browser

        try:
            async with async_playwright() as p:
                context, browser = await create_context_with_cookies(p, cookie_file)
                page = await context.new_page()
                # 最大化窗口
                try:
                    await page.evaluate("window.moveTo(0,0); window.resizeTo(screen.width, screen.height);")
                except Exception:
                    pass
                await page.goto(
                    "https://creator.xiaohongshu.com/publish/publish?source=official",
                    wait_until="domcontentloaded",
                    timeout=60000
                )
                # 进入图文tab
                try:
                    await page.get_by_text("上传图文", exact=True).click()
                except Exception:
                    pass

                await page.wait_for_selector('input.upload-input', timeout=15000)
                # 只选图片input
                inputs = await page.query_selector_all('input.upload-input')
                found = False
                for inp in inputs:
                    accept = await inp.get_attribute('accept')
                    if accept and ('image' in accept or '.jpg' in accept or '.png' in accept or '.webp' in accept):
                        await inp.set_input_files(pics)
                        found = True
                        break
                if not found:
                    return {"success": False, "error_message": "未找到支持图片的上传 input"}

                await asyncio.sleep(5)
                await page.wait_for_selector("input.d-text", timeout=10000)
                await page.fill("input.d-text", title)
                await page.wait_for_selector("div.ql-editor", timeout=10000)
                await page.click("div.ql-editor")
                await page.evaluate(
                    """(desc) => {
                        const editor = document.querySelector('div.ql-editor');
                        if (editor) {
                            editor.innerText = desc;
                        }
                    }""",
                    desc
                )
                try:
                    await page.wait_for_selector('button.publishBtn', timeout=10000)
                    await page.click('button.publishBtn')
                except Exception as e:
                    return {"success": False, "error_message": f"未能自动点击发布按钮: {e}"}
                await asyncio.sleep(5)
                await context.close()
                await browser.close()
            return {"success": True, "error_message": ""}
        except Exception as e:
            return {"success": False, "error_message": str(e)}
