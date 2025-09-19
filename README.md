 # Buffotte v0.2.0
A Website showing stats of CS2 NFT stats &amp; noting your own transaction plan.
---
Buffotte 是一个用于抓取并存储 `buff.163.com`（CS:GO/CS2 饰品市场）商品数据的轻量级爬虫与数据接入工具。项目目标是把网页端的商品快照抓取下来，保存到 MySQL 中，方便后续的数据分析、策略回测和交易记录管理。
---

## 🚀 版本更新日志

### v0.2.0 - 多线程异步爬虫 (2025.09.20)
- ✨ **新增多线程支持**：实现多线程 + 异步并发的双重优化
- 🚀 **性能大幅提升**：5个线程可实现5倍性能提升（5线程×6并发=30个同时请求）
- 🎯 **智能页面分配**：自动将页面范围平均分配给各个线程
- 🔒 **线程安全设计**：使用线程安全的数据管理器，避免数据竞争
- ⚙️ **灵活配置**：新增 `--threads` 参数，支持环境变量配置
- 📊 **详细监控**：实时显示每个线程的工作进度和状态
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

## 快速开始

### 🔥 多线程高性能爬取（v0.2.0 推荐）

```powershell
# 使用5个线程爬取1000页（推荐配置）
python .\crawler\buff_to_mysql_async.py --max-pages 1000 --threads 5

# 高性能配置：10个线程爬取2000页
python .\crawler\buff_to_mysql_async.py --max-pages 2000 --threads 10

# 保守配置：3个线程爬取500页（避免被封IP）
python .\crawler\buff_to_mysql_async.py --max-pages 500 --threads 3
```

### 📊 性能对比
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

   - 创建数据库（示例）
   ```sql
   CREATE DATABASE IF NOT EXISTS buffotte CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
   ```

   **配置优先级**：命令行参数 > 环境变量 > config.json > 默认值

   - 本项目支持多种配置方式，优先级从高到低：
     1. 命令行参数（如 `--threads 8`）
     2. 环境变量（如 `BUFF_THREADS=8`）
     3. config.json 文件配置
     4. 程序默认值

   **环境变量列表**：

     - `BUFF_DB_HOST`（默认：localhost）
     - `BUFF_DB_PORT`（默认：3306）
     - `BUFF_DB_USER`（默认：root）
     - `BUFF_DB_PASSWORD`（默认：123456）
     - `BUFF_DB_DATABASE`（默认：buffotte）
     - `BUFF_DB_TABLE`（默认：items）
     - `BUFF_START_PAGE`（默认：1）
     - `BUFF_CONCURRENCY`（默认：6，每个线程的异步并发数）
     - `BUFF_THREADS`（默认：5，线程数量）⭐新增
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
   $env:BUFF_THREADS=8          # 设置8个线程
   $env:BUFF_CONCURRENCY=10     # 每个线程10个并发
   
   # 执行爬取
   python .\crawler\buff_to_mysql_async.py --max-pages 1000 --threads 8
   ```

3) 导出登录 cookie（当抓取页面需要登录时）

   - 推荐使用 `login_and_export_cookies.py`（Playwright）导出 cookie 到 `cookies/cookies.txt`，或手动从浏览器复制。

4) 运行抓取

   **多线程版本（推荐）：**
   ```powershell
   # 使用config.json默认配置
   python .\crawler\buff_to_mysql_async.py --max-pages 1000
   
   # 指定配置文件和覆盖参数
   python .\crawler\buff_to_mysql_async.py --config .\config.json --max-pages 1000 --threads 5
   
   # 高性能配置：10个线程爬取2000页
   python .\crawler\buff_to_mysql_async.py --max-pages 2000 --threads 10
   
   # 仅测试：4个线程爬取20页
   python .\crawler\buff_to_mysql_async.py --max-pages 20 --threads 4
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

## ⚠️ 注意事项

- **封IP风险**：线程数和并发数过高可能导致IP被封，建议从保守配置开始
- **内存占用**：每个线程会创建独立的HTTP客户端，内存占用会相应增加
- **推荐配置**：
  - 日常使用：3-5个线程
  - 高性能抓取：8-10个线程
  - 测试环境：2-3个线程

## Roadmap（后续里程碑）

- ✅ 0.2.0：多线程异步爬虫，性能大幅提升，支持灵活的线程数配置
- 🔄 0.3.0：断点续传与进度文件（支持从上次中断处继续抓取），更友好的配置方式（支持 `config.json` / 环境变量）
- 📋 0.4.0：代理池 + 更智能的速率限制（自动根据 429 反馈调整并发），以及抓取策略插件化
- 🗄️ 0.5.0：历史数据版本控制（记录商品在不同时间点的快照），更完整的数据模型与索引优化

## 贡献与注意事项

- 若要复现/测试 CI，请先在环境中安装依赖：`pip install -r requirements.txt`。
- 欢迎提交 issue 或 PR，描述清楚复现步骤与期望行为。

---


