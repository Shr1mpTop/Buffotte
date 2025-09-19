import argparse
import json
import os
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=None, help='输出 cookie 文件路径（优先于 config.json 中的 cookie_file）')
    parser.add_argument('--chrome-path', default=None, help='可选：指定本地 Chrome 可执行文件路径，例如 "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"')
    args = parser.parse_args()

    # 尝试读取根目录 config.json
    cfg = {}
    try:
        with open('config.json', 'r', encoding='utf-8') as cf:
            cfg = json.load(cf)
    except FileNotFoundError:
        cfg = {}

    # 决定最终 chrome_path 与 output 路径：CLI 优先，其次 config.json
    chrome_path = args.chrome_path if args.chrome_path else cfg.get('chrome_path')
    output = args.output if args.output else cfg.get('cookie_file', 'cookies.txt')

    # 确保输出目录存在
    out_dir = os.path.dirname(output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with sync_playwright() as p:
        try:
            if chrome_path:
                browser = p.chromium.launch(headless=False, executable_path=chrome_path)
            else:
                browser = p.chromium.launch(headless=False)
        except Exception as e:
            print('启动浏览器失败：', e)
            print('如果您没有下载 Playwright 自带的浏览器，请先运行 `python -m playwright install`，或者传入 --chrome-path 指定本地 Chrome。')
            return
        context = browser.new_context()
        page = context.new_page()
        page.goto('https://buff.163.com/market/csgo')
        print('浏览器已打开，请在新窗口中完成登录操作。登录完成后，回到这里按回车继续导出 cookie...')
        input()

        cookies = context.cookies()
        # 过滤出 domain 为 .buff.163.com 或 buff.163.com 的 cookie（保留所有 cookie，写入 name=value 格式）
        with open(output, 'w', encoding='utf-8') as f:
            for c in cookies:
                f.write(f"{c['name']}={c['value']}\n")
        print('cookie 已导出到', output)
        browser.close()


if __name__ == '__main__':
    main()
