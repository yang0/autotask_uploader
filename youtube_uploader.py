try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

from typing import Dict, Any
import asyncio
import json
import os
from playwright.async_api import async_playwright

@register_node
class YouTubeVideoUploadNode(Node):
    NAME = "YouTube Video Upload"
    DESCRIPTION = "Upload a video to YouTube using Playwright automation."
    CATEGORY = "YouTube"

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
            "description": "Title of the video (max 100 characters).",
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
        "made_for_kids": {
            "label": "Made for Kids",
            "description": "Whether the video is made for kids.",
            "type": "BOOLEAN",
            "required": False,
            "default": False,
        },
        "cookie_file": {
            "label": "Cookie File Path",
            "description": "Path to the YouTube cookies JSON file.",
            "type": "STRING",
            "required": True,
            "widget": "FILE",
        },
    }

    OUTPUTS = {
        "success": {
            "label": "Success",
            "description": "Whether the upload was successful.",
            "type": "BOOL",
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
        made_for_kids = node_inputs.get("made_for_kids", False)
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

                workflow_logger.info("Navigating to YouTube Studio...")
                await page.goto("https://studio.youtube.com", timeout=60000)

                workflow_logger.info("Opening upload dialog...")
                float_btn = await page.query_selector('div.ytcp-button-shape-impl__button-text-content:text("创建")')
                if float_btn:
                    await float_btn.click()
                    await asyncio.sleep(1)
                    workflow_logger.info("Clicked floating upload button")
                else:
                    workflow_logger.warning("Floating upload button not found")

                upload_menu = await page.query_selector('tp-yt-paper-item[test-id="upload-beta"]')
                if upload_menu:
                    await upload_menu.click()
                    await asyncio.sleep(1)
                    workflow_logger.info("Clicked upload menu item")
                else:
                    workflow_logger.warning("Upload menu item not found")

                workflow_logger.info("Uploading video file...")
                file_input = await page.query_selector('input[type="file"]')
                if not file_input:
                    raise Exception("Upload input not found")
                await file_input.set_input_files(video_path)
                workflow_logger.info("Video file selected")

                # Wait for title input to appear
                await page.wait_for_selector('div#textbox[contenteditable="true"][aria-label*="添加一个可描述你视频的标题"]', timeout=60000)
                title_box = await page.query_selector('div#textbox[contenteditable="true"][aria-label*="添加一个可描述你视频的标题"]')
                if title_box:
                    await title_box.click()
                    await title_box.evaluate('(el, value) => { el.innerText = value; el.dispatchEvent(new Event("input", { bubbles: true })); }', title[:100])
                    workflow_logger.info("Title filled")
                else:
                    workflow_logger.warning("Title input not found")

                desc_box = await page.query_selector('div#textbox[contenteditable="true"][aria-label*="向观看者介绍你的视频"]')
                if desc_box:
                    await desc_box.click()
                    await desc_box.evaluate('(el, value) => { el.innerText = value; el.dispatchEvent(new Event("input", { bubbles: true })); }', description)
                    workflow_logger.info("Description filled")
                else:
                    workflow_logger.warning("Description input not found")

                if tags:
                    workflow_logger.info("Setting video tags...")
                    show_more = await page.query_selector('ytcp-button[aria-label="Show more"]')
                    if show_more:
                        await show_more.click()
                        await asyncio.sleep(1)
                        tag_input = await page.query_selector('input[aria-label="Tags"]')
                        if tag_input:
                            await tag_input.fill(','.join(tags))
                            workflow_logger.info("Tags filled")
                        else:
                            workflow_logger.warning("Tag input not found")
                    else:
                        workflow_logger.warning("Show more button not found")

                workflow_logger.info("Setting kids content status...")
                if made_for_kids:
                    kids_radio = await page.query_selector('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_MFK"]')
                    if kids_radio:
                        await kids_radio.click()
                        workflow_logger.info("Selected 'Made for kids'")
                    else:
                        workflow_logger.warning("'Made for kids' radio not found")
                else:
                    kids_radio = await page.query_selector('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]')
                    if kids_radio:
                        await kids_radio.click()
                        workflow_logger.info("Selected 'Not made for kids'")
                    else:
                        workflow_logger.warning("'Not made for kids' radio not found")

                workflow_logger.info("Proceeding through upload steps...")
                for i in range(3):
                    continue_btn = await page.query_selector('div.ytcp-button-shape-impl__button-text-content:text("继续")')
                    if continue_btn:
                        await continue_btn.click()
                        workflow_logger.info(f"Clicked Continue {i+1}")
                        await asyncio.sleep(2)
                    else:
                        workflow_logger.warning(f"Continue button {i+1} not found")
                        break

                workflow_logger.info("Setting video visibility to PUBLIC...")
                public_radio = await page.query_selector('tp-yt-paper-radio-button[name="PUBLIC"]')
                if public_radio:
                    await public_radio.click()
                    await asyncio.sleep(1)
                    workflow_logger.info("Selected PUBLIC visibility")
                else:
                    workflow_logger.warning("PUBLIC radio button not found")

                workflow_logger.info("Publishing video...")
                publish_btn = await page.query_selector('div.ytcp-button-shape-impl__button-text-content:text("发布")')
                if publish_btn:
                    await publish_btn.click()
                    await asyncio.sleep(2)
                    workflow_logger.info("Clicked publish button")
                else:
                    workflow_logger.warning("Publish button not found")

                # Wait longer after publishing to ensure completion
                await asyncio.sleep(10)
                await context.close()
                await browser.close()

                return {
                    "success": True,
                    "message": "Video upload process completed. Please verify on YouTube Studio."
                }

        except Exception as e:
            workflow_logger.error(f"YouTube upload failed: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }
