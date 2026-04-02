import time
import json
import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# 确保 playwright 能找到 chromium（安装在 root 的缓存目录）
if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/root/.cache/ms-playwright"

_CHROMIUM_HEADLESS = (
    "/root/.cache/ms-playwright/chromium_headless_shell-1208"
    "/chrome-headless-shell-linux64/chrome-headless-shell"
)
_CHROMIUM_FULL = (
    "/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"
)


class DailyKlineCrawler:
    """
    通过 playwright/chromium 绕过 Aliyun WAF 获取每日市场 K 线数据。

    策略：
      导航到 steamdt.com/section?type=BROAD，该页面自然发起 statistics/v2/chart
      XHR 请求。通过 page.route() 拦截该请求，将 URL 重写为 statistics/v1/kline，
      从而获取完整 7 字段 OHLCV 数据：
      [timestamp, open, close, high, low, volume, turnover]
    """

    def _sync_fetch_daily(self, timestamp_ms: int) -> Optional[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("❌ playwright 未安装，请运行: pip install playwright && playwright install chromium")
            return None

        _exe = _CHROMIUM_HEADLESS if os.path.exists(_CHROMIUM_HEADLESS) else _CHROMIUM_FULL
        captured_result: dict = {}

        def handle_response(response):
            """捕获被重写后的 v1/kline 响应（URL 仍包含 v1/kline）"""
            if "statistics/v1/kline" in response.url and not captured_result:
                try:
                    data = response.json()
                    if data.get("success") and data.get("data"):
                        captured_result["result"] = data
                except Exception:
                    pass

        def rewrite_to_v1_kline(route):
            """拦截 v2/chart 请求，重写 URL 为 v1/kline"""
            import re
            url = route.request.url
            new_url = url.replace("/statistics/v2/chart", "/statistics/v1/kline")
            # 移除 dateType 参数（v1/kline 不需要）
            new_url = re.sub(r'[&?]dateType=[^&]*', '', new_url)
            route.continue_(url=new_url)

        with sync_playwright() as p:
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
                # 拦截 v2/chart 请求 → 重写为 v1/kline
                page.route("**/statistics/v2/chart**", rewrite_to_v1_kline)

                try:
                    page.goto(
                        "https://steamdt.com/section?type=BROAD",
                        wait_until="load",
                        timeout=40000,
                    )
                except Exception:
                    pass

                # 等待页面加载并触发 XHR
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                for _ in range(40):
                    if captured_result:
                        break
                    page.wait_for_timeout(500)

            finally:
                browser.close()

        result = captured_result.get("result")
        if result:
            items = result.get("data", [])
            fields = len(items[0]) if items else 0
            print(f"原始数据（{len(items)} 条，每条 {fields} 字段）：")
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("处理失败: 无法从页面捕获 v1/kline 数据")
        return result

    def fetch_daily_data(self, timestamp_s: Optional[int] = None) -> Optional[dict]:
        """抓取每日K线数据，使用 playwright 拦截并重写 v2/chart → v1/kline。"""
        if timestamp_s is None:
            timestamp_s = int(time.time())
        timestamp_ms = timestamp_s * 1000

        fn = lambda: self._sync_fetch_daily(timestamp_ms)
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = executor.submit(fn).result()
        return result


if __name__ == "__main__":
    crawler = DailyKlineCrawler()
    data = crawler.fetch_daily_data()
    if data:
        print(f"\n✅ 成功获取 {len(data.get('data', []))} 条K线数据")
    else:
        print("\n❌ 获取失败")
