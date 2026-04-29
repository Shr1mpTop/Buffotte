# CS2 饰品交易平台 API & 交易 BOT 可行性调研

> 调研时间：2026-04-28
> 数据来源：各平台官方公告、Steamworks 文档、开发者社区

---

## 一、平台手续费对比

详见 [price.md](./price.md)，以下为简要汇总：

| 平台 | 卖家交易手续费 | 提现手续费 | 提现最低 | 单笔上限 |
|------|--------------|-----------|---------|---------|
| 网易 BUFF | 1.5% | 1%（最低 2 元） | 2 元 | 5 万元 |
| IGXE | 0.6% | 0.8%（最低 2 元） | 2 元 | 1 万元 |
| C5GAME | 1.0%（VIP 0.5%） | 1%（最低 2 元） | 2 元 | 5 万元 |
| 悠悠有品 | 1% | 1%（最低 2 元） | 10 元 | 2 万元 |
| CSFloat（海外） | 2.0% | 0.5%-2.5%（动态） | — | — |

**关键发现：**
- IGXE 交易手续费最低（0.6%），适合作为买入平台
- 悠悠有品交易手续费较低，但提现额度限制较大（单笔 2 万，单日 3 次）
- 所有国内平台均执行「仅出售所得资金可提现」的监管要求

---

## 二、Steam 交易机制

### 2.1 Trade Hold（7 天交易冷却）

Steam 对 CS2 饰品强制执行 7 天交易冷却：

- 购买/交易后的饰品，**7 天内不可再次交易或上架** Steam 社区市场
- 冷却期内饰品**仍可在游戏内使用**
- 这是 Steam 官方的反欺诈措施，**无法绕过**

**对搬砖的影响：**
- 买入饰品后必须持有至少 7 天才能卖出
- 7 天内价格可能波动，存在价格风险
- 高频/日内交易策略完全不可行

### 2.2 Trade Protection（2025 新增）

2025 年 Steam 引入的 Trade Protection 机制：

- CS2 饰品购买后有 7 天"交易保护"标记
- 保护期内**不能上架 Steam 社区市场**
- 交易可被撤回（7 天内），触发后账号进入 30 天冷却期
- 撤回交易会**回滚所有在 7 天窗口内的合格交易**

### 2.3 第三方平台交易流程

第三方平台（BUFF/C5/IGXE）的交易流程不经过 Steam 社区市场，而是通过 Steam 交易报价（Trade Offer）完成：

1. 买家在第三方平台付款 → 平台托管资金
2. 卖家发送 Steam 交易报价给买家（或平台 BOT）
3. 买家确认接收交易报价
4. 平台释放资金给卖家

这个流程仍然受 Steam 的 7 天 Trade Hold 限制。

---

## 三、Steam 官方 API 可用性

### 3.1 可用的 API 端点

| API 端点 | 功能 | 认证要求 |
|----------|------|---------|
| `IEconService/GetTradeOffers/v1` | 查询交易报价列表 | Steam Web API Key |
| `IEconService/GetTradeOffer/v1` | 查询单笔交易报价详情 | Steam Web API Key |
| `IEconService/GetTradeStatus/v1` | 查询交易状态 | Steam Web API Key |
| `ISteamEconomy/GetAssetClassInfo/v1` | 获取物品信息 | Steam Web API Key |
| Steam Community Market 搜索接口 | 查询市场价格 | 无需认证（有频率限制） |

**官方文档：**
- [Steamworks IEconService](https://partner.steamgames.com/doc/webapi/ieconservice)
- [Valve Developer Wiki](https://developer.valvesoftware.com/wiki/Steam_Web_API/IEconService)

### 3.2 发送交易报价

**重要：Steam 没有提供官方的"发送交易报价"API。**

发送交易报价只能通过：
- POST `https://steamcommunity.com/tradeoffer/new/send`（非官方 Web 接口）
- 需要模拟浏览器登录态（`steamLoginSecure` Cookie）
- 需要处理 Steam Guard 2FA 确认

主流开源库：
- **Node.js**: [node-steam-tradeoffer-manager](https://github.com/DoctorMcKay/node-steam-tradeoffer-manager)
- **Python**: [steam](https://github.com/ValvePython/steam)

### 3.3 频率限制

- Steam Web API：每 IP 每分钟约 100 次请求
- Steam Community Market：更严格的频率限制，高频请求会触发 IP 封禁
- 2FA 确认：每次交易需要独立的 2FA 确认码

---

## 四、第三方平台 API 可用性

### 4.1 网易 BUFF（BUFF163）

- **官方 API：无公开文档**
- **移动端 API**：存在内部 API（可通过抓包获取），但未公开，违反 ToS
- **自动交易风险**：高。BUFF 严格检测自动化行为，封号风险极高
- **数据获取**：Buffotte 项目通过 SteamDT 间接获取 BUFF 价格数据

### 4.2 C5GAME

- **官方 API：无公开文档**
- **自动交易风险**：高
- **数据获取**：可通过 SteamDT 或网页爬虫获取价格

### 4.3 IGXE

- **官方 API：无公开文档**
- **自动交易风险**：高
- **数据获取**：可通过 SteamDT 或网页爬虫获取价格

### 4.4 SteamDT（数据源）

- 提供 CS2 饰品 K 线数据 API
- Buffotte 已通过 Playwright 爬虫绕过 WAF 获取数据
- 数据覆盖 BUFF/C5/IGXE 等多平台价格

---

## 五、自动交易 BOT 可行性结论

### 5.1 结论：不建议构建自动交易 BOT

**原因：**

1. **法律合规风险**
   - 第三方平台（BUFF/C5/IGXE）均无公开 API，自动化交易违反平台服务条款
   - 可能导致账号永久封禁、资金冻结
   - 涉及资金交易的自动化操作可能触及金融监管

2. **技术壁垒**
   - Steam 发送交易报价无官方 API，需要模拟浏览器登录态
   - Steam Guard 2FA 增加了自动化复杂度
   - Steam 持续更新反自动化措施（如 Trade Protection）

3. **7 天 Trade Hold 限制**
   - 买入后必须持有 7 天，无法实现高频交易
   - 7 天内价格波动不可控，纯 BOT 交易风险高
   - Trade Reversal 机制增加了交易不确定性

4. **资金安全风险**
   - 自动 BOT 可能因 Bug 造成非预期交易
   - 价格剧烈波动时 BOT 可能来不及反应
   - 建仓/清仓策略在 7 天持有期约束下效果有限

### 5.2 推荐方案：数据分析辅助人工决策

| 能力 | 可行性 | 实现方式 |
|------|--------|---------|
| 价格监控 & 对比 | ✅ 完全可行 | 爬虫 + 数据库 |
| 利润计算 & 排行 | ✅ 完全可行 | LGBM 预测 + 费率计算 |
| 价格趋势分析 | ✅ 完全可行 | K 线数据 + 技术指标 |
| 周期性饰品识别 | ✅ 完全可行 | 历史数据统计分析 |
| 半自动提醒 | ✅ 可行 | 利润率达到阈值时推送通知 |
| 全自动交易 | ❌ 不建议 | 法律风险 + 技术壁垒 + Trade Hold |

### 5.3 开源工具参考

| 项目 | 说明 |
|------|------|
| [awesome-cs2-trading](https://github.com/redlfox/awesome-cs2-trading) | CS2 交易工具和库的精选列表 |
| [node-steam-tradeoffer-manager](https://github.com/DoctorMcKay/node-steam-tradeoffer-manager) | Node.js Steam 交易报价管理（仅限个人账号） |
| [steam (Python)](https://github.com/ValvePython/steam) | Python Steam 客户端库 |

> **注意：** 以上开源库仅适用于管理个人 Steam 账号的交易，不应用于商业化的自动交易平台。

---

## 六、搬砖策略建议

基于 7 天 Trade Hold 的约束，可行的策略包括：

### 6.1 跨平台价差套利

在低费率平台买入（如 IGXE 0.6%），在高价平台卖出（如 BUFF）。

**示例：**
- IGXE 买入 ¥100 饰品
- 7 天后 BUFF 卖出 ¥108
- BUFF 手续费：108 × 1.5% = ¥1.62
- 实际到账：¥106.38
- BUFF 提现费：106.38 × 1% = ¥2（最低 2 元）
- **净利润：106.38 - 2 - 100 = ¥4.38**
- **利润率：4.38%**（7 天），**年化 ≈ 228%**

### 6.2 周期性波动操作

利用箱子、贴纸等量大饰品的周期性价格波动。

**适合的饰品特征：**
- 成交量大、流动性好
- 价格呈周期性波动（如每周/每月规律）
- 在多个平台均有交易

### 6.3 风险提示

- 7 天持有期内价格可能大幅波动
- Steam 更新/运营活动可能剧烈影响饰品价格
- 平台费率可能随时调整
- 建议仅投入可承受损失的资金
