import time
import json
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from urllib.parse import quote
from dotenv import load_dotenv
from typing import Optional

logger = logging.getLogger(__name__)

load_dotenv()

# 确保 playwright 能找到 chromium（安装在 root 的缓存目录）
if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/root/.cache/ms-playwright"

# chromium headless shell 路径
_CHROMIUM_HEADLESS = (
    "/root/.cache/ms-playwright/chromium_headless_shell-1208"
    "/chrome-headless-shell-linux64/chrome-headless-shell"
)
_CHROMIUM_FULL = (
    "/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"
)


class DailyKlineCrawler:
    KLINE_URL = "https://api.steamdt.com/user/steam/category/v1/kline"

    def _sync_fetch_item_kline(
        self,
        item_id: str,
        platform: str = "BUFF",
        type_day: str = "2",
        hashname: str = None,
    ) -> Optional[dict]:
        """
        使用 playwright/chromium 绕过 Aliyun WAF 获取 K 线数据。

        策略（与 buff-tracker ddrager.py 相同）：
        1. 导航到 steamdt.com 物品页面，让浏览器完成 WAF JS 挑战。
        2. 通过 page.on("response") 拦截 kline API 响应。
        3. 若页面未自然触发目标 kline 请求，则回退到在浏览器上下文内
           用 page.evaluate() 发起 fetch，确保 WAF 认可。
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("playwright 未安装，请运行: pip install playwright && playwright install chromium")
            return None

        # 导航目标：有 hashname 就去物品详情页，否则去首页
        nav_url = (
            f"https://steamdt.com/cs2/{quote(hashname)}"
            if hashname
            else "https://steamdt.com"
        )
        captured_result: dict = {}

        def handle_response(response):
            if "/kline" in response.url and not captured_result:
                try:
                    data = response.json()
                    if data.get("success") and data.get("data"):
                        captured_result["result"] = data
                except Exception:
                    pass

        with sync_playwright() as p:
            # 优先用 headless shell，回退到全功能 chromium
            _exe = _CHROMIUM_HEADLESS if os.path.exists(_CHROMIUM_HEADLESS) else _CHROMIUM_FULL
            browser = p.chromium.launch(
                executable_path=_exe,
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            try:
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/145.0.0.0 Safari/537.36"
                    ),
                    locale="zh-CN",
                    viewport={"width": 1920, "height": 1080},
                )
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};
                """)
                page = context.new_page()
                page.on("response", handle_response)

                # 导航以通过 WAF JS 挑战
                try:
                    page.goto(nav_url, wait_until="domcontentloaded", timeout=30000)
                except Exception:
                    pass

                # 等待最多 15 秒看是否自然捕获到 kline 响应
                for _ in range(30):
                    if captured_result:
                        break
                    page.wait_for_timeout(500)

                # 回退：若未捕获，则从浏览器上下文内主动发起 fetch
                if not captured_result:
                    ts = str(int(time.time() * 1000))
                    fetch_url = (
                        f"https://api.steamdt.com/user/steam/category/v1/kline"
                        f"?timestamp={ts}&type={type_day}&maxTime=0"
                        f"&typeVal={item_id}&platform={platform}&specialStyle="
                    )
                    try:
                        result = page.evaluate("""
                            async (url) => {
                                const resp = await fetch(url, {
                                    headers: {
                                        'accept': '*/*',
                                        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                                        'language': 'zh_CN',
                                        'x-app-version': '1.0.0',
                                        'x-currency': 'CNY',
                                        'x-device': '1',
                                    },
                                    credentials: 'include'
                                });
                                return await resp.json();
                            }
                        """, fetch_url)
                        logger.info("原始数据获取成功")
                        if result.get("success") and result.get("data"):
                            captured_result["result"] = result
                        else:
                            logger.error("处理失败: 无效的 JSON 数据")
                    except Exception as e:
                        logger.error(f"fetch 失败: {e}")
            finally:
                browser.close()

        return captured_result.get("result")

    def fetch_item_details(
        self,
        item_id: str,
        platform: str = "BUFF",
        type_day: str = "2",
        date_type: int = 3,
        hashname: str = None,
    ) -> Optional[dict]:
        """抓取物品 K 线数据，使用 playwright 绕过 Aliyun WAF。"""
        fn = partial(self._sync_fetch_item_kline, item_id, platform, type_day, hashname)
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = executor.submit(fn).result()
        if result:
            logger.info("成功获取 K 线数据")
        else:
            logger.error("获取 K 线数据失败")
        return result


if __name__ == "__main__":
    crawler = DailyKlineCrawler()
    item_id = "22349"
    item_data = crawler.fetch_item_details(item_id)
    if item_data:
        logger.info("物品详情抓取成功!")
    else:
        logger.error("物品详情抓取失败!")