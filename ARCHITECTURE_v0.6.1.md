# Buffotte v0.6.1 架构文档

## 🏗️ 模块化架构概览

Buffotte v0.6.1 采用了全新的模块化架构设计，将原来的单体应用拆分为清晰的功能模块，提高了代码的可维护性和可扩展性。

## 📁 项目结构

```
Buffotte/
├── backend/                # 后端服务 (Node.js + Express)
│   ├── config/
│   │   └── database.js     # 数据库配置
│   ├── database/
│   │   └── connection.js   # 数据库连接池
│   ├── routes/
│   │   ├── search.js       # 搜索路由
│   │   ├── items.js        # 物品详情路由
│   │   └── stats.js        # 统计数据路由
│   ├── services/
│   │   └── crawlerService.js # 爬虫服务
│   ├── server.js           # 主服务器入口
│   └── package.json
├── frontend/               # 前端界面 (Vue 3 + Vite)
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBox.vue
│   │   │   └── ItemDetail.vue
│   │   └── App.vue
│   └── package.json
├── crawler/                # 爬虫模块 (Python)
│   ├── core.py             # 核心爬虫功能
│   ├── database.py         # 数据库操作
│   ├── single_item_updater.py # 单品更新
│   ├── batch_crawler.py    # 批量爬取
│   ├── main.py             # 统一入口
│   └── requirements.txt    # Python依赖
├── config.json             # 全局配置
├── deploy.bat             # Windows部署脚本
├── deploy.sh              # Linux部署脚本
└── README.md
```

## 🔧 模块详解

### 后端模块化 (Backend)

#### 1. 配置层 (`config/`)
- **database.js**: 统一的数据库配置和环境变量管理

#### 2. 数据层 (`database/`)
- **connection.js**: MySQL连接池管理，提供统一的数据库访问接口

#### 3. 路由层 (`routes/`)
- **search.js**: 处理饰品搜索相关的API请求
- **items.js**: 处理单个饰品详情和刷新操作
- **stats.js**: 处理统计数据和价格分布图表

#### 4. 服务层 (`services/`)
- **crawlerService.js**: 封装爬虫调用逻辑，处理路径解析和进程管理

#### 5. 应用入口 (`server.js`)
- 模块化的Express应用，负责路由注册和中间件配置

### 爬虫模块化 (Crawler)

#### 1. 核心功能 (`core.py`)
```python
# 主要功能
- load_config_json()      # 配置加载
- load_cookie_file()      # Cookie管理
- fetch_page()            # 页面爬取
- search_item_by_name()   # 物品搜索
```

#### 2. 数据库操作 (`database.py`)
```python
# 主要功能
- get_db_config_from_dict()  # 配置转换
- writer_loop()              # 异步数据写入
```

#### 3. 单品更新 (`single_item_updater.py`)
```python
# 主要功能
- update_single_item()       # 单个物品更新
```

#### 4. 批量爬取 (`batch_crawler.py`)
```python
# 主要功能
- main()                     # 批量爬取主函数
- crawl_pages_range()        # 页面范围爬取
```

#### 5. 统一入口 (`main.py`)
```python
# 命令行接口
python main.py single "AK-47 | 红线"     # 单品更新
python main.py batch --max-pages 100   # 批量爬取
```

## 🔗 模块间通信

### 1. 前端 → 后端
- **搜索**: `/api/search?q=物品名称`
- **详情**: `/api/item/:id`
- **刷新**: `/api/item/refresh`
- **统计**: `/api/stats`

### 2. 后端 → 爬虫
- 通过`crawlerService.js`调用Python脚本
- 使用子进程管理，支持超时控制
- 正确的路径解析和工作目录设置

### 3. 爬虫 → 数据库
- 异步写入队列，提高性能
- 连接池管理，避免连接泄露
- 事务支持，保证数据一致性

## 🚀 部署和启动

### 自动部署
```bash
# Windows
deploy.bat

# Linux/Mac
./deploy.sh
```

### 手动启动
```bash
# 后端
cd backend && npm start

# 前端
cd frontend && npm run dev

# 爬虫 - 批量模式
cd crawler && python main.py batch --max-pages 100

# 爬虫 - 单品模式
cd crawler && python main.py single "AK-47 | 红线"
```

## 🎯 架构优势

### 1. 可维护性
- **模块分离**: 每个模块职责单一，便于维护
- **代码复用**: 公共功能抽取为独立模块
- **错误隔离**: 单个模块的问题不会影响整个系统

### 2. 可扩展性
- **水平扩展**: 各模块可独立部署和扩展
- **功能扩展**: 新功能可以独立模块的形式添加
- **技术栈灵活**: 各模块可选择最适合的技术

### 3. 开发效率
- **并行开发**: 不同模块可由不同开发者并行开发
- **测试友好**: 模块化便于单元测试和集成测试
- **部署简化**: 自动化部署脚本，一键部署

### 4. 性能优化
- **资源隔离**: 各模块资源使用独立，避免相互影响
- **缓存策略**: 可为不同模块设计不同的缓存策略
- **负载均衡**: 支持多实例部署和负载均衡

## 🔮 未来规划

1. **微服务化**: 进一步将模块拆分为独立的微服务
2. **容器化**: 支持Docker部署
3. **监控系统**: 添加模块级别的监控和日志
4. **API网关**: 统一API管理和认证
5. **分布式缓存**: Redis集群支持
6. **消息队列**: 异步任务处理优化