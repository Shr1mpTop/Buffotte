# 如何获取物品价格数据

## 概述

基于 `test.py` 的实践经验，本文档记录使用 SteamDT API 获取 CS2 物品价格数据的爬虫方法。该方法通过 POST 请求调用 `https://api.steamdt.com/user/steam/type-trend/v2/item/details` 端点，获取指定物品的详细价格趋势数据。

## 参数说明

- `itemId`: 物品的唯一 ID（从 SteamDT 网站 URL 或 API 获取）。
- `platform`: 平台，如 "BUFF"。
- `typeDay`: 时间类型，如 "1"（日线）。
- `dateType`: 数据类型，如 3（可能表示某种趋势）。
- `timestamp`: 当前时间戳（毫秒）。

## 注意事项

- **API 密钥**: 需要有效的 `access-token`，否则请求可能失败。建议从环境变量加载以提高安全性。
- **速率限制**: SteamDT API 可能有请求频率限制，建议添加延迟或重试机制。
- **错误处理**: 代码已包含基本异常处理，实际使用时可扩展。
- **合法性**: 确保遵守 SteamDT 的使用条款，避免滥用。

## 实践经验

- 从 `test.py` 测试中，POST body 必须包含完整参数，否则 API 返回错误。
- 时间戳需为毫秒级字符串。
- 头部信息需模拟浏览器请求，以避免被拦截。
- 数据格式为 JSON，包含 `success`、`data` 等字段。

## 原始数据
{
    "success": true,
    "data": [
        [
            "1765043769",
            170.0,**buff当前价**
            186,**buff在售数量**
            149.0,**buff求购价**
            50,**buff求购**
            4074.42,**成交额**
            21,**成交量**
            "63749"**存世量**
        ],
        [
            "1765044369",
            170.0,
            186,
            149.0,
            50,
            null,
            null,
            "63749"
        ]
    ],
    "errorCode": 0,
    "errorMsg": null,
    "errorData": null,
    "errorCodeStr": null
}