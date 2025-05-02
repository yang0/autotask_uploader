try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

from typing import Dict, Any, Optional, Tuple
import asyncio
import json
import os
from playwright.async_api import Page, Browser, BrowserContext
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

@register_node
class DouyinVideoUploadNode(Node):
    NAME = "Douyin Video Upload"
    DESCRIPTION = "Upload a video to Douyin using Playwright automation."
    CATEGORY = "Douyin"

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
            "required": False,
        },
        "cookie_file": {
            "label": "Cookie File Path",
            "description": "Path to the Douyin cookies JSON file.",
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
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        self.logger = workflow_logger
        try:
            video_path = node_inputs["video_path"]
            title = node_inputs["title"]
            description = node_inputs["description"]
            tags = self._parse_tags(node_inputs.get("tags", ""))
            cookie_file = node_inputs["cookie_file"]

            if not os.path.exists(video_path):
                return self._error_response(f"Video file not found: {video_path}")

            if not os.path.exists(cookie_file):
                return self._error_response(f"Cookie file not found: {cookie_file}")

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                try:
                    context = await self._create_context_with_cookies(browser, cookie_file)
                    page = await context.new_page()
                    
                    # Navigate and wait for initial load
                    await self._navigate_to_upload_page(page)
                    
                    # Upload video and fill details
                    await self._upload_video(page, video_path)
                    await self._fill_video_details(page, title, description, tags)
                    
                    # Wait for upload completion and publish
                    success = await self._publish_video(page)
                    if not success:
                        return self._error_response("Failed to publish video")
                    
                    return {
                        "success": True,
                        "message": "Video upload process completed. Please verify on Douyin.",
                        "value": True
                    }
                finally:
                    await browser.close()
        except Exception as e:
            self.logger.error(f"Douyin upload failed: {str(e)}")
            return self._error_response(str(e))

    def _parse_tags(self, tags: str) -> list:
        if not tags:
            return []
        if isinstance(tags, str):
            try:
                return json.loads(tags)
            except json.JSONDecodeError:
                return [t.strip() for t in tags.split(",") if t.strip()]
        return tags

    def _error_response(self, message: str) -> Dict[str, Any]:
        self.logger.error(message)
        return {"success": False, "message": message, "value": False}

    async def _navigate_to_upload_page(self, page: Page) -> None:
        await page.goto("https://creator.douyin.com/creator-micro/home")
        try:
            # Wait for and click upload button if needed
            upload_button = await page.wait_for_selector("div.title-HvY9Az", timeout=10000)
            if upload_button:
                await upload_button.click()
                self.logger.info("Clicked upload entry button")
        except PlaywrightTimeoutError:
            self.logger.info("Already on upload page or using different layout")

    async def _upload_video(self, page: Page, video_path: str) -> None:
        try:
            # First wait for the upload container
            await page.wait_for_selector('div.container-drag-title-p6mssi', timeout=20000)
            self.logger.info("Found upload container")
            
            # Then find and use the file input
            file_input = await page.query_selector('input[type="file"]')
            if not file_input:
                raise Exception("File input element not found")
                
            await file_input.set_input_files(video_path)
            self.logger.info("Video file upload started")
        except PlaywrightTimeoutError as e:
            raise Exception("Could not find upload container") from e
        except Exception as e:
            raise Exception(f"Failed to upload video: {str(e)}") from e

    async def _fill_video_details(self, page: Page, title: str, description: str, tags: list) -> None:
        # Fill title with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await page.wait_for_selector('input.semi-input.semi-input-default', timeout=20000)
                title_input = await page.query_selector('input.semi-input.semi-input-default')
                await title_input.click()
                await title_input.fill(title)
                self.logger.info("Title filled")
                break
            except PlaywrightTimeoutError as e:
                if attempt == max_retries - 1:
                    raise Exception("Could not find title input after multiple attempts") from e
                await asyncio.sleep(2)

        # Fill description and tags with full selector
        try:
            desc_selector = 'div.zone-container.editor-kit-container.editor.editor-comp-publish.notranslate.chrome.window.chrome88'
            await page.wait_for_selector(desc_selector, timeout=20000)
            desc_input = await page.query_selector(desc_selector)
            if not desc_input:
                raise Exception("Description input element not found")
            
            await desc_input.click()
            await desc_input.fill(description)
            
            if tags:
                tag_text = ' '.join([f'#{tag}' if not tag.startswith('#') else tag for tag in tags])
                await desc_input.type(' ' + tag_text)
            self.logger.info("Description and tags filled")
        except PlaywrightTimeoutError as e:
            raise Exception("Could not find description input") from e
        except Exception as e:
            raise Exception(f"Failed to fill description: {str(e)}") from e

    async def _publish_video(self, page: Page) -> bool:
        try:
            # Wait for video processing with Chinese text
            await page.wait_for_selector('div:has-text("预览视频")', timeout=120000)
            self.logger.info("Video preview available")
            await asyncio.sleep(2)
            
            # Click publish button
            publish_selector = 'button.button-dhlUZE.primary-cECiOJ.fixed-J9O8Yw'
            await page.wait_for_selector(publish_selector, timeout=20000)
            publish_btn = await page.query_selector(publish_selector)
            
            if not publish_btn:
                self.logger.error("Publish button not found")
                return False
            
            btn_text = await publish_btn.inner_text()
            if "发布" in btn_text:
                await publish_btn.click()
                self.logger.info("Publish button clicked")
                await asyncio.sleep(5)
                return True
            else:
                self.logger.error("Publish button text mismatch")
                return False
        except PlaywrightTimeoutError as e:
            self.logger.error(f"Timeout while publishing: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error during publishing: {str(e)}")
            return False

    async def _create_context_with_cookies(self, browser: Browser, cookie_file: str) -> BrowserContext:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, dict) and ('cookies' in data or 'origins' in data):
            return await browser.new_context(storage_state=cookie_file)
        elif isinstance(data, list):
            context = await browser.new_context()
            await context.add_cookies(data)
            return context
        else:
            return await browser.new_context()
