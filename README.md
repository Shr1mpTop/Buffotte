 # Buffotte v0.4.0
A Website showing stats of CS2 NFT stats &amp; noting your own transaction plan.
---
Buffotte 是一个用于抓取并存储 `buff.163.com`（CS:GO/CS2 饰品市场）商品数据的轻量级爬虫与数据接入工具。项目目标是把网页端的商品快照抓取下来，保存到 MySQL 中，方便后续的数据分析、策略回测和交易记录管理。
---

## 🚀 版本更新日志

### v0.4.0 - 代理池 + 智能速率限制 (2025.09.20)
- 🔄 **代理池管理**：支持代理轮换、健康检查、自动故障切换 ⭐**重要功能**
- 🧠 **智能速率限制**：根据429错误自动调整并发数，避免被封禁 ⭐**重要功能**
- 📊 **实时监控**：提供代理池和速率限制的详细统计信息
- ⚡ **动态调整**：遇到限制时自动降低并发，成功时逐步恢复
- 🛡️ **防封策略**：指数退避、延迟机制、错误统计等多重保护
- 🔧 **灵活配置**：支持独立启用代理池或速率限制功能
- 📋 **详细文档**：提供完整的配置说明和最佳实践指南

### v0.3.0 - 价格历史数据支持 (2025.09.20)
- 📊 **价格历史记录**：新增独立价格历史表 `items_price_history`，记录每次爬取的价格变化 ⭐**重要功能**
- 🔍 **历史数据分析**：支持价格趋势分析、市场波动监控、投资机会发现
- 💾 **双表设计**：主表保持最新数据，历史表记录所有价格变化，支持高效联查询
- ⚙️ **灵活控制**：通过 `enable_price_history` 配置项控制是否启用价格历史功能
- 📋 **丰富查询**：提供多种联查询示例，支持价格趋势、波动分析、投资策略等场景
- 🗄️ **数据完整性**：保持原有数据结构完全兼容，渐进式升级
- 🔧 **配置优先级修复**：修复命令行参数默认值覆盖config.json的问题，现在正确支持配置文件默认值 ⭐**重要修复**

### v0.2.0 - 多线程异步爬虫 (2025.09.20)
- ✨ **新增多线程支持**：实现多线程 + 异步并发的双重优化
- 🚀 **性能大幅提升**：5个线程可实现5倍性能提升（5线程×6并发=30个同时请求）
- 🎯 **智能页面分配**：自动将页面范围平均分配给各个线程
- 🔒 **线程安全设计**：使用线程安全的数据管理器，避免数据竞争
- ⚙️ **灵活配置**：新增 `--threads` 参数，支持环境变量配置
- 📋 **配置文件支持**：支持config.json配置文件，多级配置优先级
- 🔍 **详细监控**：实时显示每个线程的工作进度和状态
- 🔄 **向下兼容**：保留原有单线程版本，所有配置保持兼容

### v0.1.0 - 基础功能
- 基于网站内部 API 批量抓取商品列表数据
- 支持 cookie（登录态）以获取需要登录才能查看的页面
- 异步并发抓取 + 单写入线程批量写入 MySQL（避免并发写冲突）
- 支持将抓取结果写入 MySQL（ON DUPLICATE KEY UPDATE 做到幂等写入）

## 仓库结构
- `crawler/`：主要抓取脚本，`buff_to_mysql_async.py` 为异步并发抓取并写入 MySQL 的主脚本
- `cookies/`：示例 cookie 存放（请不要提交真实 cookie 到仓库）
- `requirements.txt`：Python 依赖
- `config.json`：配置文件，包含数据库连接、线程数、价格历史、代理池等配置
- `PROXY_RATE_LIMIT_README.md`：代理池和智能速率限制功能详细说明 ⭐**v0.4.0新增**
- `PRICE_HISTORY_README.md`：价格历史功能详细说明和联查询示例 ⭐**v0.3.0新增**
- `MULTI_THREAD_README.md`：多线程功能详细说明
- `CHANGELOG.md`：详细版本更新日志

## 快速开始

### 🔥 智能速率限制 + 多线程爬取（v0.4.0 推荐）

```powershell
# 使用智能速率限制，自动避免429错误
python .\crawler\buff_to_mysql_async.py --max-pages 500 --threads 3

# 高性能配置：启用代理池 + 智能速率限制
python .\crawler\buff_to_mysql_async.py --max-pages 2000 --threads 10

# 保守配置：3个线程爬取500页（避免被封IP）
python .\crawler\buff_to_mysql_async.py --max-pages 500 --threads 3
```

### 📊 数据存储结构
- **主表 `items`**：存储最新商品信息，快速查询当前状态
- **历史表 `items_price_history`**：记录所有价格变化，支持趋势分析
- **联查询支持**：可以轻松分析价格走势、市场波动、投资机会

### 🚀 性能对比
- **单线程版本**：1线程 × 6并发 = 最多6个同时请求
- **多线程版本**：5线程 × 6并发 = 最多30个同时请求 ⚡**性能提升5倍**

### ⚙️ 环境准备

1) 创建并激活 Python 环境（可选使用 conda 或 venv）

   使用 venv：

   ```powershell
   python -m venv .venv
   pip install -r requirements.txt
   ```

2) 配置数据库和参数

   **方式一：使用config.json（推荐）**
   
   项目根目录下的 `config.json` 已包含默认配置：
   ```json
   {
     "max_pages": 200,
     "start_page": 1,
     "concurrency": 6,
     "threads": 5,
     "no_db": false,
     "enable_price_history": true,
     "cookie_file": "./cookies/cookies.txt",
     "chrome_path": "C:/Program Files/Google/Chrome/Application/chrome.exe",
     "proxy_file": null,
     "db": {
       "host": "localhost",
       "port": 3306,
       "user": "root",
       "password": "123456",
       "database": "buffotte",
       "table": "items"
     }
   }
   ```
   
   **方式二：使用环境变量**

   - 创建数据库（示例）
   ```sql
   CREATE DATABASE IF NOT EXISTS buffotte CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
   ```

   **配置优先级**：命令行参数 > 环境变量 > config.json > 默认值

   - 本项目支持多种配置方式，优先级从高到低：
     1. **命令行参数**（如 `--threads 8 --max-pages 1000`）最高优先级
     2. **环境变量**（如 `BUFF_THREADS=8`）
     3. **config.json 文件配置**（如 `"threads": 5`）
     4. **程序默认值**（如 threads=5, max_pages=2000）

   ⭐ **重要更新**：现在不指定命令行参数时，会正确使用config.json中的默认值，而不是程序硬编码的默认值。

   **环境变量列表**：

     - `BUFF_DB_HOST`（默认：localhost）
     - `BUFF_DB_PORT`（默认：3306）
     - `BUFF_DB_USER`（默认：root）
     - `BUFF_DB_PASSWORD`（默认：123456）
     - `BUFF_DB_DATABASE`（默认：buffotte）
     - `BUFF_DB_TABLE`（默认：items）
     - `BUFF_START_PAGE`（默认：1）
     - `BUFF_CONCURRENCY`（默认：6，每个线程的异步并发数）
     - `BUFF_THREADS`（默认：5，线程数量）⭐v0.2.0新增
     - `BUFF_ENABLE_PRICE_HISTORY`（默认：true，启用价格历史记录）⭐v0.3.0新增
     - `BUFF_COOKIE_FILE`（默认：./cookies/cookies.txt）
     - `BUFF_PROXY_FILE`（可选）
     - `BUFF_NO_DB`（布尔，接受 1/true/yes/on，默认：False）
     - `BUFF_MAX_PAGES`（默认：2000；但 CLI `--max-pages` 将优先）

   PowerShell 设置示例（当前会话）：

   ```powershell
   # 基础配置
   $env:BUFF_DB_HOST='localhost'
   $env:BUFF_DB_USER='root'
   $env:BUFF_DB_PASSWORD='123456'
   $env:BUFF_COOKIE_FILE='./cookies/cookies.txt'
   
   # 多线程配置（可选）
   $env:BUFF_THREADS=8                    # 设置8个线程
   $env:BUFF_CONCURRENCY=10               # 每个线程10个并发
   $env:BUFF_ENABLE_PRICE_HISTORY='true'  # 启用价格历史记录（v0.3.0）
   
   # 执行爬取
   python .\crawler\buff_to_mysql_async.py --max-pages 1000 --threads 8
   ```

3) 导出登录 cookie（当抓取页面需要登录时）

   - 推荐使用 `login_and_export_cookies.py`（Playwright）导出 cookie 到 `cookies/cookies.txt`，或手动从浏览器复制。

4) 运行抓取

   **多线程版本（推荐）：**
   ```powershell
   # 使用config.json默认配置（200页，5线程）
   python .\crawler\buff_to_mysql_async.py
   
   # 只覆盖页面数，线程数使用config.json默认值
   python .\crawler\buff_to_mysql_async.py --max-pages 1000
   
   # 只覆盖线程数，页面数使用config.json默认值
   python .\crawler\buff_to_mysql_async.py --threads 3
   
   # 指定配置文件和覆盖参数
   python .\crawler\buff_to_mysql_async.py --config .\config.json --max-pages 1000 --threads 5
   
   # 高性能配置：10个线程爬取2000页
   python .\crawler\buff_to_mysql_async.py --max-pages 2000 --threads 10
   ```
   
   **单线程版本（兼容）：**
   ```powershell
   # 设置1个线程回退到单线程模式
   python .\crawler\buff_to_mysql_async.py --max-pages 200 --threads 1
   ```

   **命令行参数说明**：
   - `--max-pages`: 总共要爬取的页面数
   - `--threads`: 线程数量，默认5个
   - `--config`: 配置文件路径，默认 `./config.json`

   说明：脚本现在支持多线程并发抓取，每个线程负责不同的页面范围。运行时会显示详细的线程分配和进度信息。

## 🎯 多线程工作原理

### 页面分配策略
假设要爬取100页，使用5个线程：
- 线程1：负责页面 1-20
- 线程2：负责页面 21-40  
- 线程3：负责页面 41-60
- 线程4：负责页面 61-80
- 线程5：负责页面 81-100

### 双重并发机制
1. **线程级并发**：多个线程同时运行，每个线程独立的事件循环
2. **异步级并发**：每个线程内部使用 asyncio.Semaphore 控制并发数

### 监控输出示例
```
开始多线程爬取: 4 个线程，总共 20 页 (页面 1-20)
线程 1: 负责页面 1-5 (共 5 页)
线程 2: 负责页面 6-10 (共 5 页)
线程 3: 负责页面 11-15 (共 5 页)
线程 4: 负责页面 16-20 (共 5 页)
...
线程 1 - page 1: 获取到 20 条记录
...
所有爬取线程已完成
```

## 📊 价格历史功能

### 🎯 核心特性
- **独立历史表**: 在 `items` 表基础上新增 `items_price_history` 表
- **完整价格记录**: 每次爬取都会记录完整的价格快照到历史表
- **灵活查询**: 支持各种历史价格分析和趋势查询
- **零影响**: 不影响现有的 `items` 表结构和查询性能

### 📋 数据结构
```sql
-- 主表：存储最新数据（保持不变）
items (id, name, sell_min_price, buy_max_price, updated_at, ...)

-- 历史表：记录所有价格变化（新增）
items_price_history (
  id AUTO_INCREMENT,
  item_id,                    -- 关联商品ID
  sell_reference_price,       -- 历史参考价格
  sell_min_price,            -- 历史最低售价
  buy_max_price,             -- 历史最高求购价
  recorded_at                -- 记录时间
)
```

### 🔍 联查询示例
```sql
-- 查看商品价格趋势（近7天）
SELECT 
    i.name,
    ph.sell_min_price,
    ph.recorded_at
FROM items i
JOIN items_price_history ph ON i.id = ph.item_id
WHERE i.id = 33815 
  AND ph.recorded_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY ph.recorded_at DESC;

-- 找出价格波动最大的商品
SELECT 
    i.name,
    MAX(ph.sell_min_price) - MIN(ph.sell_min_price) as price_volatility
FROM items i
JOIN items_price_history ph ON i.id = ph.item_id
WHERE ph.recorded_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY i.id, i.name
ORDER BY price_volatility DESC;
```

📖 更多查询示例请参考 [PRICE_HISTORY_README.md](./PRICE_HISTORY_README.md)

## ⚠️ 注意事项

- **封IP风险**：线程数和并发数过高可能导致IP被封，建议从保守配置开始
- **内存占用**：每个线程会创建独立的HTTP客户端，内存占用会相应增加
- **价格历史存储**：启用价格历史会增加数据库存储需求，建议定期清理旧数据（v0.3.0）
- **推荐配置**：
  - 日常使用：3-5个线程
  - 高性能抓取：8-10个线程
  - 测试环境：2-3个线程

## 📊 价格历史分析示例（v0.3.0）

```sql
-- 查看商品最近的价格变化
SELECT 
    i.name,
    i.sell_min_price as current_price,
    ph.sell_min_price as history_price,
    ph.recorded_at
FROM items i
LEFT JOIN items_price_history ph ON i.id = ph.item_id
WHERE i.name LIKE '%AK-47%'
ORDER BY ph.recorded_at DESC
LIMIT 10;

-- 分析价格波动最大的商品
SELECT 
    i.name,
    MIN(ph.sell_min_price) as min_price_24h,
    MAX(ph.sell_min_price) as max_price_24h,
    ((MAX(ph.sell_min_price) - MIN(ph.sell_min_price)) / MIN(ph.sell_min_price) * 100) as volatility_percent
FROM items i
JOIN items_price_history ph ON i.id = ph.item_id
WHERE ph.recorded_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY i.id, i.name
ORDER BY volatility_percent DESC
LIMIT 10;
```

详细查询示例请查看 `PRICE_HISTORY_README.md`

## Roadmap（后续里程碑）

- ✅ 0.2.0：多线程异步爬虫，性能大幅提升，支持灵活的线程数配置
- ✅ 0.3.0：价格历史数据支持，独立历史表，支持趋势分析和联查询
- 🔄 0.4.0：断点续传与进度文件（支持从上次中断处继续抓取）
- 📋 0.5.0：代理池 + 更智能的速率限制（自动根据 429 反馈调整并发），以及抓取策略插件化
- 🗄️ 0.6.0：数据可视化仪表板，价格趋势图表，投资策略回测功能

## 贡献与注意事项

- 若要复现/测试 CI，请先在环境中安装依赖：`pip install -r requirements.txt`。
- 欢迎提交 issue 或 PR，描述清楚复现步骤与期望行为。

---


