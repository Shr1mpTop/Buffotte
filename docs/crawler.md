# 爬虫系统

## 概述

Buffotte 使用 Playwright 驱动 Chromium 浏览器绕过阿里云 WAF 防护，从 SteamDT 抓取 CS2 市场数据。爬虫分为两个模块：

| 模块 | 文件 | 用途 |
|------|------|------|
| 大盘爬虫 | `crawler/daily_crawler.py` | 抓取 CS2 市场整体 K 线数据 |
| 饰品爬虫 | `crawler/item_price.py` | 抓取单个饰品的价格趋势 |

## 技术原理

### WAF 绕过策略

SteamDT 使用阿里云 WAF 进行 JavaScript 挑战验证。直接 HTTP 请求会被拦截，因此采用 Playwright 模拟真实浏览器：

1. **启动 Chromium** — 配置反检测参数（隐藏 webdriver 特征）
2. **导航到目标页面** — 浏览器自动完成 WAF JS 挑战
3. **拦截 API 响应** — 通过 `page.on("response")` 捕获 XHR 请求返回的数据
4. **回退机制** — 若未自然触发请求，则在浏览器上下文内用 `page.evaluate(fetch)` 主动发起

### 反检测配置

```python
# 隐藏自动化特征
context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};
""")
```

## 大盘爬虫 (DailyKlineCrawler)

### 工作流程

```
导航 steamdt.com/section?type=BROAD
    │
    ├── 拦截 v2/chart 请求 → URL 重写为 v1/kline
    │   （v1 接口返回完整的 7 字段 OHLCV 数据）
    │
    ├── 等待捕获响应（最多 20 秒）
    │
    └── 返回 [timestamp, open, close, high, low, volume, turnover] 数据
```

### 使用方式

```python
from crawler.daily_crawler import DailyKlineCrawler

crawler = DailyKlineCrawler()
data = crawler.fetch_daily_data()

# data 格式
# {
#     "success": true,
#     "data": [
#         ["1757346910", 1554.01, 1551.89, 1558.66, 1551.89, "2203908", 110775711.58],
#         ...
#     ]
# }
```

## 饰品爬虫 (ItemPriceCrawler)

### 工作流程

```
导航 steamdt.com/mkt?search={hashname}
    │
    ├── 拦截 /kline 响应
    │
    ├── 等待捕获（最多 15 秒）
    │
    ├── 若未捕获 → 浏览器内 fetch 发起请求
    │
    └── 返回饰品价格数据
```

### 数据格式

```json
{
    "success": true,
    "data": [
        [
            "1765043769",   // 时间戳
            170.0,          // BUFF 当前售价
            186,            // BUFF 在售数量
            149.0,          // BUFF 求购价
            50,             // BUFF 求购数
            4074.42,        // 成交额
            21,             // 成交量
            "63749"         // 存世量
        ]
    ]
}
```

### 使用方式

```python
from crawler.item_price import DailyKlineCrawler

crawler = DailyKlineCrawler()
data = crawler.fetch_item_details(
    item_id="22349",
    platform="BUFF",
    type_day="2",
    hashname="AK-47 | Redline (Field-Tested)"
)
```

## 部署注意

- **容器环境**: Playwright 的 Chromium 二进制安装在 `/root/.cache/ms-playwright/`，Dockerfile 已处理依赖
- **内存需求**: Chromium headless 至少需要 512MB 内存
- **超时控制**: 页面加载超时 30-40 秒，数据捕获超时 15-20 秒
- **并发限制**: 使用 `ThreadPoolExecutor(max_workers=1)` 限制并发，避免被 WAF 封禁
