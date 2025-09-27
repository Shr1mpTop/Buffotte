# 🎮 Buffotte - CS:GO饰品价格分析系统# 🎮 Buffotte - CS:GO饰品价格分析系统# 🎮 Buffotte - CS:GO饰品价格分析系统



**版本：v1.0.0**



一个完整的CS:GO饰品价格数据采集、分析和可视化系统，采用现代化技术栈构建。**版本：v0.8.0****版本：v0.6.1**



![License](https://img.shields.io/badge/license-MIT-blue.svg)

![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)

![Vue.js](https://img.shields.io/badge/vue.js-3+-green.svg)一个完整的CS:GO饰品价格数据采集、分析和可视化系统，包含网页爬虫、数据存储和Web界面。一个完整的CS:GO饰品价格数据采集、分析和可视化系统，包含网页爬虫、数据存储和Web界面。

![Python](https://img.shields.io/badge/python-3.8+-green.svg)

![MySQL](https://img.shields.io/badge/mysql-8.0+-blue.svg)



## ✨ 核心功能![License](https://img.shields.io/badge/license-MIT-blue.svg)![License](https://img.shields.io/badge/license-MIT-blue.svg)



- 📊 **实时数据可视化** - 现代化Vue.js仪表板![Python](https://img.shields.io/badge/python-3.8+-green.svg)![Python](https://i## 🎯 版本更新日志

- 📈 **多周期K线图** - 小时/日/周K线数据展示

- 🤖 **智能数据爬虫** - Python异步多线程采集![Node.js](https://img.shields.io/badge/node.js-16+-green.svg)

- 🔄 **RESTful API** - 完整的后端数据接口

- 🐳 **容器化部署** - Docker一键部署![Vue.js](https://img.shields.io/badge/vue.js-3+-green.svg)### v0.6.1 - 模块化重构 (2025-09-20)

- ⚡ **高性能架构** - Node.js + Vue.js + MySQL

- 🔧 **代码重构**：将爬虫和后端代码进行模块化拆分

## 🏗️ 项目架构

## ✨ 主要功能- 📦 **爬虫模块化**：

```

buffotte/  - `crawler/core.py` - 核心爬虫功能

├── backend/           # Node.js后端服务

│   ├── src/🔍 **智能搜索** - 模糊搜索饰品，实时显示价格信息    - `crawler/database.py` - 数据库操作

│   │   ├── routes/    # API路由

│   │   ├── services/  # 业务逻辑🕷️ **数据采集** - 异步多线程爬虫，支持代理池和智能限流    - `crawler/single_item_updater.py` - 单品更新

│   │   └── utils/     # 工具函数

│   ├── config/        # 配置文件📊 **数据分析** - 价格分布可视化，实时统计分析    - `crawler/batch_crawler.py` - 批量爬取

│   ├── scripts/       # 部署脚本

│   ├── Dockerfile     # 容器配置🌐 **Web界面** - Vue 3 + ECharts 现代化界面    - `crawler/main.py` - 统一入口

│   └── package.json

├── crawler/           # Python数据爬虫📈 **价格历史** - 记录价格变化，支持趋势分析  - 🏗️ **后端模块化**：

│   ├── src/           # 爬虫源码

│   ├── config/        # 爬虫配置  - `backend/routes/` - 路由模块化

│   ├── Dockerfile     # 爬虫容器

│   └── requirements.txt## 🚀 快速启动  - `backend/services/` - 服务层分离

├── frontend/          # Vue.js前端应用

│   ├── src/           # 前端源码  - `backend/database/` - 数据库连接管理

│   ├── public/        # 静态资源

│   ├── Dockerfile     # 前端容器### 1. 环境要求  - `backend/config/` - 配置管理

│   └── package.json

├── scripts/           # 项目级脚本- Python 3.8+ - 🐛 **路径修复**：修复搜索功能中的路径解析问题

│   ├── dev.sh         # Linux开发脚本

│   └── dev.bat        # Windows开发脚本- Node.js 16+- 📚 **部署优化**：添加自动部署脚本和依赖管理

├── docker/            # Docker配置

├── docs/              # 项目文档- MySQL 5.7+

├── .env.example       # 环境变量模板

├── docker-compose.yml # 容器编排- Anaconda/Miniconda（推荐）### v0.6.0 - 智能搜索功能 (2025-09-20)

└── README.md

```- 🔍 **智能搜索**：新增饰品模糊搜索功能，支持实时建议和自动完成



## 🚀 快速开始### 2. 安装依赖- 📊 **详情展示**：显示具体饰品的详细价格信息，包括收购价、售价、成交量



### 环境要求```bash- 🔄 **数据刷新**：集成爬虫实现一键刷新饰品最新价格数据



- Node.js 18+git clone https://github.com/Shr1mpTop/Buffotte.git- 🎨 **UI优化**：新增搜索框和饰品详情卡片，提升用户体验

- Python 3.8+

- MySQL 8.0+cd Buffotte- ⚡ **API扩展**：新增搜索、饰品详情、数据刷新等RESTful接口

- Docker & Docker Compose (可选)



### 一键安装

# 创建conda环境### v0.5.0 - Web界面发布 (2025-09-20)

```bash

# 克隆项目conda create -n buffotte python=3.11- 🌐 **全新Web界面**：基于Vue 3 + ECharts的现代化界面

git clone https://github.com/Shr1mpTop/Buffotte.git

cd buffotteconda activate buffotte- 📊 **价格分布可视化**：饼状图展示不同价格区间的饰品分布



# 安装所有依赖pip install -r requirements.txt- 📈 **实时统计面板**：显示总饰品数、平均价格、价格范围等关键指标

./scripts/dev.sh install

# Windows: scripts\dev.bat install```- 🎨 **响应式设计**：完美适配桌面和移动设备

```

- ⚡ **高性能架构**：Node.js后端 + Vue前端的现代化技术栈

### 配置环境

### 3. 配置数据库- 🔌 **RESTful API**：提供完整的数据接口，支持第三方集成s.io/badge/python-3.8+-green.svg)

```bash

# 复制环境变量```sql![Node.js](https://img.shields.io/badge/node.js-16+-green.svg)

cp .env.example .env

CREATE DATABASE buffotte CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;![Vue.js](https://img.shields.io/badge/vue.js-3+-green.svg)

# 编辑数据库配置

vim .env```

```

## ✨ 功能特性

### 初始化数据库

编辑 `config.json` 配置数据库连接信息。

```bash

# 创建数据库### 🔍 智能搜索

./scripts/dev.sh db:init

### 4. 启动应用- **饰品搜索**：模糊搜索饰品名称，实时显示建议

# 运行数据爬虫

./scripts/dev.sh crawl- **详情查看**：显示具体饰品的价格、数量、成交信息

```

#### 🔥 一键启动（推荐）- **数据刷新**：一键刷新获取最新价格（集成爬虫）

### 启动服务

```bash

```bash

# 一键启动所有服务# Windows用户：双击运行### 🕷️ 数据采集

./scripts/dev.sh start

快速启动.bat- **智能爬虫**：异步多线程爬取Buff饰品数据

# 或分别启动

./scripts/dev.sh stop  # 先停止- **代理池支持**：自动管理代理，提高采集稳定性

npm start &           # 后端

npm run dev &         # 前端# 或使用菜单式启动器- **智能限流**：自适应速率控制，避免被封禁

```

start.bat- **增量更新**：支持价格历史记录

访问 http://localhost:5173 查看应用

```

## 🐳 Docker部署

### 📊 数据分析

```bash

# 构建并启动#### 手动启动- **实时价格分布**：饼状图展示不同价格区间的饰品分布

docker-compose up -d

```bash- **统计信息**：总数量、平均价格、最高/最低价格等

# 查看日志

docker-compose logs -f# 启动后端（3001端口）- **响应式设计**：适配桌面和移动设备



# 停止服务cd backend && npm install && npm run dev

docker-compose down

```### 🏗️ 技术架构



## 📊 API文档# 启动前端（5173端口）  - **后端**：Node.js + Express + MySQL



### 获取总体统计cd frontend && npm install && npm run dev- **前端**：Vue 3 + Vite + ECharts

```

GET /api/stats```- **爬虫**：Python + asyncio + httpx

Response: {

  "total_items": 12345,- **数据库**：MySQL with 价格历史表

  "average_price": 123.45

}访问 http://localhost:5173 开始使用！

```

## 🚀 快速开始

### 获取K线数据

```### 5. 数据采集（可选）

GET /api/kline/{type}  # type: hour, day, week

Response: [```bash### 环境要求

  {

    "timestamp": 1634567890000,# 基础爬取- Python 3.8+

    "open_price": 100.0,

    "high_price": 105.0,python crawler/main.py batch --max-pages 100- Node.js 16+

    "low_price": 95.0,

    "close_price": 102.0,- MySQL 5.7+

    "volume": 1000,

    "turnover": 100000.0# 单个物品更新

  }

]python crawler/main.py single "AK-47 | 红线"### 1. 克隆项目

```

``````bash

### 获取物品列表

```git clone https://github.com/Shr1mpTop/Buffotte.git

GET /api/items

Response: [## 📁 项目结构cd Buffotte

  {

    "id": 1,```

    "name": "AK-47 | Redline",

    "BUFF": "150.00",```

    "C5": "145.00"

  }Buffotte/### 2. 配置数据库

]

```├── 📁 backend/              # Node.js后端服务```bash



## 🛠️ 开发指南├── 📁 frontend/             # Vue3前端界面  # 创建MySQL数据库



### 添加新API├── 📁 crawler/              # Python爬虫模块mysql -u root -p



1. 在 `backend/src/routes/` 创建路由文件├── 📁 docs/                 # 📚 详细文档CREATE DATABASE buffotte CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

2. 在 `backend/src/services/` 实现业务逻辑

3. 在 `server.js` 中注册路由├── 📁 cookies/              # Cookie管理```



### 数据爬虫开发├── config.json              # 配置文件



1. 在 `crawler/src/` 添加爬虫脚本├── start.bat                # 启动脚本### 3. 运行爬虫（可选）

2. 更新 `requirements.txt`

3. 在 `scripts/dev.sh` 添加执行命令├── 快速启动.bat              # 一键启动```bash



### 前端开发└── requirements.txt         # Python依赖# 安装Python依赖



1. 在 `frontend/src/` 添加组件```pip install -r requirements.txt

2. 使用Vue 3 Composition API

3. 通过 `/api/*` 调用后端接口



## 📋 开发脚本## 📚 文档中心# 配置cookies（如需要）



```bash# 编辑 cookies/cookies.txt

# 安装依赖

./scripts/dev.sh install详细文档请查看 [`docs/`](./docs/) 目录：



# 启动服务# 运行爬虫

./scripts/dev.sh start

| 文档 | 说明 |python crawler/buff_to_mysql_async.py --max-pages 100

# 停止服务

./scripts/dev.sh stop|------|------|```



# 运行爬虫| [📖 文档索引](./docs/README.md) | 完整文档导航 |

./scripts/dev.sh crawl

| [🚀 启动指南](./docs/STARTUP_README.md) | 详细启动说明 |### 4. 启动后端服务

# 初始化数据库

./scripts/dev.sh db:init| [🏗️ 架构设计](./docs/ARCHITECTURE_v0.6.1.md) | v0.6.1架构文档 |```bash

```

| [🔍 搜索功能](./docs/SEARCH_FEATURE_README.md) | 搜索功能说明 |cd backend

## 🎯 版本特性

| [📊 价格历史](./docs/PRICE_HISTORY_README.md) | 价格历史分析 |npm install

### v1.0.0 - 现代化重构

- 🏗️ **全新架构** - 模块化后端 + 容器化部署| [🌐 部署指南](./docs/WEBSITE_README.md) | 网站部署说明 |npm start

- 📊 **多周期K线** - 小时/日/周K线数据支持

- ⚡ **高性能API** - Node.js + MySQL优化```

- 🎨 **现代化前端** - Vue 3 + 响应式设计

- 🐳 **容器化** - Docker完整支持## 🎯 版本历程后端服务运行在：http://localhost:3001

- 📚 **完善文档** - 详细的开发和部署指南



### v0.8.0 - 智能并发爬取

- 🚀 **智能并发** - 多账户状态管理### v0.6.1 - 模块化重构 (2025-09-20)### 5. 启动前端服务

- 🛡️ **429处理** - 自动错误恢复

- 📋 **队列管理** - FIFO任务调度- 🔧 **代码重构**：爬虫和后端模块化拆分```bash



### v0.5.0 - Web界面发布- 🏗️ **架构优化**：routes/services/config 分层设计cd frontend

- 🌐 **Vue界面** - 现代化Web界面

- 📊 **数据可视化** - ECharts图表展示- 🐛 **问题修复**：路径解析、依赖管理优化npm install

- 📈 **实时统计** - 动态数据面板

- 📚 **文档完善**：统一启动脚本和详细文档npm run dev

## 🤝 贡献指南

```

1. Fork 项目

2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)### v0.6.0 - 智能搜索 (2025-09-20)  前端界面访问：http://localhost:3000

3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)

4. 推送到分支 (`git push origin feature/AmazingFeature`)- 🔍 **智能搜索**：模糊搜索、实时建议、一键刷新

5. 创建 Pull Request

- 📊 **详情展示**：完整价格信息、成交数据## 📁 项目结构

## 📄 许可证

- 🎨 **UI优化**：现代化界面设计

本项目采用 MIT 许可证

```

## ⚠️ 免责声明

### v0.5.0 - Web界面 (2025-09-20)Buffotte/

本项目仅供学习和研究使用。请遵守相关网站的使用条款和法律法规。

- 🌐 **全新界面**：Vue 3 + ECharts 可视化├── 📁 backend/              # Node.js后端

## 📞 联系方式

- 📈 **实时统计**：价格分布、数量统计│   ├── server.js            # Express服务器

- GitHub: [@Shr1mpTop](https://github.com/Shr1mpTop)

- 项目主页: https://github.com/Shr1mpTop/Buffotte- ⚡ **高性能**：Node.js + Vue 现代架构│   ├── package.json         # 后端依赖



---│   └── .env                 # 环境配置



⭐ 如果这个项目对你有帮助，请给它一个星标！[查看完整更新日志](./CHANGELOG.md)├── 📁 frontend/             # Vue3前端

│   ├── src/

## 🛠️ 技术栈│   │   ├── App.vue          # 主应用组件

│   │   ├── components/      # Vue组件

- **前端**: Vue 3 + Vite + ECharts + Element Plus│   │   └── style.css        # 样式文件

- **后端**: Node.js + Express + MySQL│   ├── package.json         # 前端依赖

- **爬虫**: Python + asyncio + httpx + pymysql│   └── vite.config.js       # Vite配置

- **数据库**: MySQL with 价格历史表├── 📁 crawler/              # Python爬虫

- **部署**: Docker + Nginx（可选）│   └── buff_to_mysql_async.py  # 异步爬虫主程序

├── 📁 cookies/              # Cookie文件

## 🤝 贡献指南├── config.json              # 爬虫配置

├── requirements.txt         # Python依赖

1. Fork 项目├── start-backend.bat        # Windows后端启动脚本

2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)├── start-frontend.bat       # Windows前端启动脚本

3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)└── README.md                # 项目说明

4. 推送分支 (`git push origin feature/AmazingFeature`)```

5. 创建 Pull Request

## 🛠️ 配置说明

## 📄 许可证

### 数据库配置

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情编辑 `backend/.env` 文件：

```env

## ⚠️ 免责声明DB_HOST=localhost

DB_PORT=3306

本项目仅供学习和研究使用。请遵守相关网站的使用条款和法律法规。DB_USER=root

DB_PASSWORD=your_password

## 📞 联系方式DB_DATABASE=buffotte

PORT=3001

- GitHub: [@Shr1mpTop](https://github.com/Shr1mpTop)```

- 项目主页: [https://github.com/Shr1mpTop/Buffotte](https://github.com/Shr1mpTop/Buffotte)

### 爬虫配置

---编辑 `config.json` 文件：

```json

⭐ 如果这个项目对你有帮助，请给它一个星标！{
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

### v0.8.0 - 智能并发爬取系统 (2025-01-20)

- 🚀 **智能并发架构**：全新设计的并发爬取系统，支持多账户智能调度
- 👥 **账户状态管理**：实现idle/busy/cooldown三种状态，智能分配任务
- 🛡️ **429错误处理**：自动检测429错误，30秒冷却后重新分配任务
- 📋 **队列管理系统**：FIFO队列确保页面按顺序处理，提高数据一致性
- ⚡ **高性能并发**：支持3个账户同时工作，显著提升采集效率
- 🔄 **智能重试机制**：失败任务自动重新入队，确保数据完整性
- 📊 **实时状态监控**：详细的账户状态和队列状态日志输出
- 🏗️ **模块化重构**：batch_crawler.py实现核心并发逻辑，代码更清晰

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

- [ ] 价格历史趋势图表
- [ ] 价格预警和通知功能
- [ ] 饰品收藏夹和关注列表
- [ ] 高级筛选和排序功能
- [ ] 支持多个游戏的饰品数据
- [ ] 移动端APP开发
- [ ] 数据导出功能

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
- ✅ 0.4.0：代理池 + 智能速率限制（自动根据429反馈调整并发）
- ✅ 0.5.0：Web界面发布，Vue 3 + ECharts现代化界面
- ✅ 0.6.0：模块化重构，代码结构优化
- ✅ 0.8.0：智能并发爬取系统，多账户状态管理和429错误处理
- � 0.9.0：数据可视化仪表板，价格趋势图表，投资策略回测功能
- 📋 1.0.0：生产就绪版本，完整的错误处理和监控系统

## 贡献与注意事项

- 若要复现/测试 CI，请先在环境中安装依赖：`pip install -r requirements.txt`。
- 欢迎提交 issue 或 PR，描述清楚复现步骤与期望行为。

---


