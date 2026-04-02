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

# chromium headless shell 路径
_CHROMIUM_HEADLESS = (
    "/root/.cache/ms-playwright/chromium_headless_shell-1208"
    "/chrome-headless-shell-linux64/chrome-headless-shell"
)
_CHROMIUM_FULL = (
    "/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"
)


class DailyKlineCrawler:
    KLINE_URL = "https://api.steamdt.com/user/statistics/v1/kline"

    def _sync_fetch_daily(self, timestamp_ms: int) -> Optional[dict]:
        """
        使用 playwright/chromium 绕过 Aliyun WAF 获取每日K线数据。

        策略（与 buff-tracker ddrager.py 相同）：
        1. 导航到 steamdt.com 首页，让浏览器完成 WAF JS 挑战。
        2. 通过 page.on("response") 拦截 statistics/v1/kline 响应。
        3. 若未自然捕获，回退到在浏览器上下文内用 page.evaluate() 发起 fetch。
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("❌ playwright 未安装，请运行: pip install playwright && playwright install chromium")
            return None

        captured_result: dict = {}

        def handle_response(response):
            if "statistics/v1/kline" in response.url and not captured_result:
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

                # 第一步：导航到 steamdt.com 首页完成 WAF JS 挑战并获取 Cookie
                try:
                    page.goto("https://steamdt.com", wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2000)
                except Exception:
                    pass

                # 第二步：直接导航到 API URL——浏览器发出完整 GET 请求
                # 携带首页已获取的 Cookie 及完整 sec-* headers，绕过 WAF
                fetch_url = (
                    f"https://api.steamdt.com/user/statistics/v1/kline"
                    f"?timestamp={timestamp_ms}&type=2&maxTime="
                )
                api_json_re = __import__("re").compile(r"\{.*\}", __import__("re").DOTALL)

                for attempt in range(3):
                    if captured_result:
                        break
                    try:
                        resp = page.goto(fetch_url, wait_until="domcontentloaded", timeout=15000)
                        if resp and resp.ok:
                            try:
                                data = resp.json()
                            except Exception:
                                raw = page.content()
                                m = api_json_re.search(raw)
                                data = json.loads(m.group()) if m else {}
                            print("原始数据：")
                            print(json.dumps(data, indent=4, ensure_ascii=False))
                            if data.get("success") and data.get("data"):
                                captured_result["result"] = data
                            else:
                                print("处理失败: 无效的 JSON 数据")
                    except Exception as e:
                        print(f"attempt {attempt+1} 失败: {e}")
                    if not captured_result:
                        page.wait_for_timeout(2000)
            finally:
                browser.close()

        return captured_result.get("result")

    def fetch_daily_data(self, timestamp_s: Optional[int] = None) -> Optional[dict]:
        """抓取每日K线数据，使用 playwright 绕过 Aliyun WAF。"""
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
        print("Success!")
    else:
        print("Failed!")