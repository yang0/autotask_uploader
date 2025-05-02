try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

from typing import Dict, Any
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

@register_node
class KuaishouVideoUploadNode(Node):
    NAME = "Kuaishou Video Upload"
    DESCRIPTION = "Upload a video to Kuaishou using Playwright automation."
    CATEGORY = "Kuaishou"

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
            "description": "Title and description of the video.",
            "type": "STRING",
            "required": True,
        },
        "tags": {
            "label": "Tags",
            "description": "List of tags for the video (comma separated or JSON array, max 3 tags).",
            "type": "STRING",
            "required": False,
        },
        "publish_time": {
            "label": "Publish Time",
            "description": "Schedule publish time in format 'YYYY-MM-DD HH:MM:SS' (optional).",
            "type": "STRING",
            "required": False,
        },
        "cookie_file": {
            "label": "Cookie File Path",
            "description": "Path to the Kuaishou cookies JSON file.",
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
        tags = node_inputs.get("tags", "")
        publish_time = node_inputs.get("publish_time", "")
        cookie_file = node_inputs["cookie_file"]

        # Process tags
        if isinstance(tags, str):
            try:
                import json
                tags = json.loads(tags)
            except Exception:
                tags = [t.strip() for t in tags.split(",") if t.strip()]
        tags = tags[:3]  # Kuaishou limits to 3 tags

        # Process publish time
        publish_date = None
        if publish_time:
            try:
                publish_date = datetime.strptime(publish_time, "%Y-%m-%d %H:%M:%S")
            except Exception as e:
                workflow_logger.warning(f"Invalid publish time format: {e}. Will use immediate publish.")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context(storage_state=cookie_file)
                page = await context.new_page()

                workflow_logger.info("Navigating to Kuaishou upload page...")
                await page.goto("https://cp.kuaishou.com/article/publish/video")
                await page.wait_for_url("https://cp.kuaishou.com/article/publish/video")

                workflow_logger.info("Initiating video upload...")
                upload_button = await page.wait_for_selector("button[class^='_upload-btn']", timeout=15000)
                async with page.expect_file_chooser() as fc_info:
                    await upload_button.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(video_path)

                await asyncio.sleep(2)

                # Handle "I know" popup if present
                try:
                    know_btn = page.locator('button[type=\"button\"] span:text(\"我知道了\")')
                    if await know_btn.count() > 0:
                        await know_btn.click()
                except Exception:
                    pass

                # Handle guide overlay
                workflow_logger.info("Handling guide overlay...")
                for _ in range(10):
                    try:
                        skip_btn = page.locator("div[role='button']:has-text('跳过')")
                        if await skip_btn.count() > 0:
                            await skip_btn.click()
                            await asyncio.sleep(1)
                            continue
                    except Exception:
                        pass
                    try:
                        next_btn = page.locator("div:has-text('下一步')")
                        if await next_btn.count() > 0:
                            await next_btn.click()
                            await asyncio.sleep(1)
                            continue
                    except Exception:
                        pass
                    try:
                        await page.evaluate("""
                            () => {
                                document.querySelectorAll('.react-joyride__spotlight, .react-joyride__overlay').forEach(e => e.remove());
                            }
                        """)
                    except Exception:
                        pass
                    if await page.locator('.react-joyride__overlay').count() == 0:
                        break
                    await asyncio.sleep(1)

                workflow_logger.info("Setting title and tags...")
                desc_input = await page.wait_for_selector("div._description_1axiz_59#work-description-edit", timeout=15000)
                await desc_input.click()
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Delete")
                await page.keyboard.type(title)
                await page.keyboard.press("Enter")
                for tag in tags:
                    await page.keyboard.type(f"#{tag} ")
                    await asyncio.sleep(1)

                workflow_logger.info("Waiting for upload completion...")
                for _ in range(60):
                    if await page.locator("text=上传中").count() == 0:
                        workflow_logger.info("Video upload completed")
                        break
                    await asyncio.sleep(2)
                else:
                    raise Exception("Video upload timeout")

                if publish_date:
                    workflow_logger.info("Setting scheduled publish time...")
                    publish_date_str = publish_date.strftime("%Y-%m-%d %H:%M:%S")
                    await page.locator("label:text('发布时间')").locator('xpath=following-sibling::div').locator(
                        '.ant-radio-input').nth(1).click()
                    await asyncio.sleep(1)
                    date_input = await page.wait_for_selector('div.ant-picker-input input[placeholder=\"选择日期时间\"]', timeout=15000)
                    await date_input.click()
                    await asyncio.sleep(1)
                    await page.keyboard.press("Control+A")
                    await page.keyboard.type(publish_date_str)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(1)

                workflow_logger.info("Publishing video...")
                publish_button = page.get_by_text("发布", exact=True)
                if await publish_button.count() > 0:
                    await publish_button.click()
                    await asyncio.sleep(1)
                    confirm_button = page.get_by_text("确认发布")
                    if await confirm_button.count() > 0:
                        await confirm_button.click()
                else:
                    raise Exception("Publish button not found")

                await asyncio.sleep(5)
                await context.close()
                await browser.close()

                return {
                    "success": True,
                    "message": "Video upload process completed. Please verify on Kuaishou."
                }

        except Exception as e:
            workflow_logger.error(f"Kuaishou upload failed: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }
