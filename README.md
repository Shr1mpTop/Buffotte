# 🎮 Buffotte - CS:GO饰品价格分析系统

**版本：v0.5.0**

一个完整的CS:GO饰品价格数据采集、分析和可视化系统，包含网页爬虫、数据存储和Web界面。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Node.js](https://img.shields.io/badge/node.js-16+-green.svg)
![Vue.js](https://img.shields.io/badge/vue.js-3+-green.svg)

## ✨ 功能特性

### 🕷️ 数据采集
- **智能爬虫**：异步多线程爬取Buff饰品数据
- **代理池支持**：自动管理代理，提高采集稳定性
- **智能限流**：自适应速率控制，避免被封禁
- **增量更新**：支持价格历史记录

### 📊 数据分析
- **实时价格分布**：饼状图展示不同价格区间的饰品分布
- **统计信息**：总数量、平均价格、最高/最低价格等
- **响应式设计**：适配桌面和移动设备

### 🏗️ 技术架构
- **后端**：Node.js + Express + MySQL
- **前端**：Vue 3 + Vite + ECharts
- **爬虫**：Python + asyncio + httpx
- **数据库**：MySQL with 价格历史表

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 5.7+

### 1. 克隆项目
```bash
git clone https://github.com/Shr1mpTop/Buffotte.git
cd Buffotte
```

### 2. 配置数据库
```bash
# 创建MySQL数据库
mysql -u root -p
CREATE DATABASE buffotte CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

### 3. 运行爬虫（可选）
```bash
# 安装Python依赖
pip install -r requirements.txt

# 配置cookies（如需要）
# 编辑 cookies/cookies.txt

# 运行爬虫
python crawler/buff_to_mysql_async.py --max-pages 100
```

### 4. 启动后端服务
```bash
cd backend
npm install
npm start
```
后端服务运行在：http://localhost:3001

### 5. 启动前端服务
```bash
cd frontend
npm install
npm run dev
```
前端界面访问：http://localhost:3000

## 📁 项目结构

```
Buffotte/
├── 📁 backend/              # Node.js后端
│   ├── server.js            # Express服务器
│   ├── package.json         # 后端依赖
│   └── .env                 # 环境配置
├── 📁 frontend/             # Vue3前端
│   ├── src/
│   │   ├── App.vue          # 主应用组件
│   │   ├── components/      # Vue组件
│   │   └── style.css        # 样式文件
│   ├── package.json         # 前端依赖
│   └── vite.config.js       # Vite配置
├── 📁 crawler/              # Python爬虫
│   └── buff_to_mysql_async.py  # 异步爬虫主程序
├── 📁 cookies/              # Cookie文件
├── config.json              # 爬虫配置
├── requirements.txt         # Python依赖
├── start-backend.bat        # Windows后端启动脚本
├── start-frontend.bat       # Windows前端启动脚本
└── README.md                # 项目说明
```

## 🛠️ 配置说明

### 数据库配置
编辑 `backend/.env` 文件：
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=buffotte
PORT=3001
```

### 爬虫配置
编辑 `config.json` 文件：
```json
{
  "max_pages": 100,
  "threads": 1,
  "enable_price_history": true,
  "db": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "buffotte"
  }
}
```

## 📖 API文档

### GET /api/health
健康检查接口
```json
{
  "success": true,
  "message": "Buffotte Backend API 运行正常",
  "timestamp": "2025-01-20T10:00:00.000Z"
}
```

### GET /api/stats
获取总体统计数据
```json
{
  "success": true,
  "data": {
    "totalItems": 12345,
    "avgPrice": 123.45,
    "minPrice": 0.03,
    "maxPrice": 50000.00,
    "totalSellOrders": 98765,
    "totalBuyOrders": 54321
  }
}
```

### GET /api/price-distribution
获取价格分布数据
```json
{
  "success": true,
  "data": [
    {"name": "¥0-10", "value": 8520},
    {"name": "¥10-50", "value": 2840},
    {"name": "¥50-100", "value": 620},
    {"name": "¥100-500", "value": 280},
    {"name": "¥500-1000", "value": 60},
    {"name": "¥1000+", "value": 25}
  ]
}
```

## 🎯 版本更新日志

### v0.5.0 - Web界面发布 (2025-09-20)
- 🌐 **全新Web界面**：基于Vue 3 + ECharts的现代化界面
- 📊 **价格分布可视化**：饼状图展示不同价格区间的饰品分布
- 📈 **实时统计面板**：显示总饰品数、平均价格、价格范围等关键指标
- 🎨 **响应式设计**：完美适配桌面和移动设备
- ⚡ **高性能架构**：Node.js后端 + Vue前端的现代化技术栈
- � **RESTful API**：提供完整的数据接口，支持第三方集成

### v0.4.0 - 代理池 + 智能速率限制
- � **代理池管理**：支持代理轮换、健康检查、自动故障切换
- 🧠 **智能速率限制**：根据429错误自动调整并发数，避免被封禁

### v0.3.0 - 价格历史数据支持
- 📊 **价格历史记录**：新增独立价格历史表，记录每次爬取的价格变化
- 🔍 **历史数据分析**：支持价格趋势分析、市场波动监控

### v0.2.0 - 多线程异步爬虫
- ✨ **多线程支持**：实现多线程 + 异步并发的双重优化
- 🚀 **性能大幅提升**：5个线程可实现5倍性能提升

## 🎯 未来计划

- [ ] 添加更多图表类型（柱状图、趋势图）
- [ ] 实现饰品搜索和筛选功能
- [ ] 添加价格预警功能
- [ ] 支持多个游戏的饰品数据
- [ ] 添加用户系统和收藏功能
- [ ] 移动端APP开发

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## ⚠️ 免责声明

本项目仅供学习和研究使用。请遵守相关网站的使用条款和法律法规。

## 📞 联系方式

- GitHub: [@Shr1mpTop](https://github.com/Shr1mpTop)
- 项目主页: [https://github.com/Shr1mpTop/Buffotte](https://github.com/Shr1mpTop/Buffotte)

---

⭐ 如果这个项目对你有帮助，请给它一个星标！

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


