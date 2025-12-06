# 如何使用爬虫
## 爬虫调用方法
基于项目中的 `daily_crawler.py` 脚本，调用方法如下：

1. **激活环境**（如果需要）：
   ```
   conda activate buffotte
   ```
2. **运行脚本**：
   ```
   python daily_crawler.py
   ```
3. **输出**：脚本会直接打印抓取的原始 JSON 数据到控制台，无需额外参数。
如果需要自定义（如指定时间戳），可以修改脚本中的 `fetch_daily_data()` 调用。

## 脚本说明

- **API**: SteamDT K线数据 (https://api.steamdt.com/user/statistics/v1/kline)
- **数据类型**: 每日 K线数据（open, high, low, close, volume, turnover）
- **依赖**: requests, python-dotenv

## 数据格式
{
    "success": true,
    "data": [
        [
            "1757346910", //timestamp
            1554.01, //open
            1551.89, //close
            1558.66, //high
            1551.89, //low
            "2203908", //volume
            110775711.58 //turnover
        ],
        [
            "1757433310",
            1551.89,
            1564.23,
            1564.23,
            1539.85,
            "2484992",
            129727462.8
        ]
    ],
"errorCode": 0,
"errorMsg": null,
"errorData": null,
"errorCodeStr": null
}