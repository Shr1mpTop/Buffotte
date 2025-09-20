# Buffotte 饰品价格分析系统

这是一个简单的 CS:GO 饰品价格分析网站，显示当前饰品价格分布的饼状图。

## 项目结构

```
Buffotte/
├── backend/          # Node.js 后端 (Express + MySQL)
├── frontend/         # Vue3 前端 (Vite + ECharts)
├── crawler/          # Python 爬虫
└── config.json       # 配置文件
```

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
npm install
```

### 2. 安装前端依赖

```bash
cd ../frontend
npm install
```

### 3. 启动后端服务

```bash
cd ../backend
npm run dev
```

后端将运行在 http://localhost:3001

### 4. 启动前端服务

```bash
cd ../frontend
npm run dev
```

前端将运行在 http://localhost:3000

## API 接口

- `GET /api/health` - 健康检查
- `GET /api/stats` - 获取统计数据
- `GET /api/price-distribution` - 获取价格分布数据

## 功能特性

- 📊 实时显示饰品价格分布饼状图
- 📈 统计总体数据（总数量、平均价格、最高/最低价格）
- 🎨 现代化的 UI 设计
- 📱 响应式布局，支持移动端

## 数据库要求

需要 MySQL 数据库，默认配置：
- 主机: localhost:3306
- 用户: root
- 密码: 123456
- 数据库: buffotte
- 表: items

可以通过修改 `backend/.env` 文件来更改数据库配置。

## 下一步计划

- [ ] 添加更多图表类型
- [ ] 实现饰品搜索功能
- [ ] 添加价格历史趋势图
- [ ] 增加数据过滤和排序功能