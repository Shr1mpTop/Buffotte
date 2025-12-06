## 后端实现

### 依赖包

```
bcrypt==5.0.0          # 密码哈希
fastapi==0.104.1       # API 框架
uvicorn==0.24.0        # ASGI 服务器
pymysql==1.1.0         # MySQL 连接
python-dotenv==1.0.0   # 环境变量管理
```

### 核心文件

#### user_manager.py

用户管理核心类，提供数据库操作功能：

```python
class UserManager:
    def __init__(self):                    # 初始化数据库连接
    def create_user_table(self):           # 创建用户表
    def generate_user_id(self, email):     # 生成用户 ID
    def hash_password(self, password):     # 密码哈希
    def register_user(self, username, email, password):  # 注册用户
    def verify_password(self, email, password):          # 验证密码
```

#### api.py (FastAPI)

REST API 接口：

- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录

### API 接口详情

#### 注册接口

**请求**: `POST /api/register`
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "success": true,
  "message": "注册成功"
}
```

#### 登录接口

**请求**: `POST /api/login`
```json
{
  "email": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "success": true,
  "message": "登录成功",
  "user": {
    "email": "string",
    "username": "string"
  }
}
```

## 前端实现

### 技术栈

- **Vue 3** + Composition API
- **Vue Router 4** - 路由管理
- **Axios** - HTTP 请求
- **Vite** - 构建工具

### 页面结构

#### 路由配置 (src/router.js)

```javascript
const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/home', component: Home },
  { path: '/profile', component: Profile }
]
```

#### 页面组件

- **Login.vue**: 登录页面
- **Register.vue**: 注册页面
- **Home.vue**: 用户首页
- **Profile.vue**: 用户信息页面

### 认证流程

1. **注册流程**:
   - 用户填写表单 → 前端验证 → 调用注册 API → 成功跳转登录页

2. **登录流程**:
   - 用户输入邮箱密码 → 调用登录 API → 获取用户信息 → 本地存储 → 跳转首页

3. **状态管理**:
   - 使用 `localStorage` 存储用户信息
   - 路由守卫检查登录状态

## 安全考虑

### 密码安全

- 使用 bcrypt 算法，包含盐值和成本因子
- 密码永不以明文存储
- 支持密码验证但不支持密码找回（需要重置机制）

### API 安全

- CORS 配置限制允许的源
- 输入验证防止 SQL 注入
- 错误信息不泄露敏感数据

### 会话管理

- 使用本地存储维护登录状态
- 敏感操作需要重新验证
- 注销时清除所有本地数据

## 部署和运行

### 环境要求

- Python 3.8+
- Node.js 16+
- MySQL 5.7+

### 安装步骤

1. **安装后端依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量** (.env 文件):
   ```
   HOST=your_mysql_host
   PORT=your_mysql_port
   USER=your_mysql_user
   PASSWORD=your_mysql_password
   DATABASE=your_database
   CHARSET=utf8mb4
   ```

3. **创建数据库表**:
   ```bash
   python user_manager.py
   ```

4. **启动后端服务器**:
   ```bash
   python api.py
   # 运行在 http://localhost:8000
   ```

5. **安装前端依赖**:
   ```bash
   cd frontend
   npm install
   ```

6. **启动前端开发服务器**:
   ```bash
   npm run dev
   # 运行在 http://localhost:5173
   ```

## 使用说明

### 用户注册

1. 访问注册页面 `/register`
2. 填写用户名、邮箱、密码
3. 点击注册按钮
4. 注册成功后跳转到登录页面

### 用户登录

1. 访问登录页面 `/login`
2. 输入注册的邮箱和密码
3. 点击登录按钮
4. 登录成功后跳转到首页

### 查看用户信息

1. 登录后访问首页 `/home`
2. 点击 "Profile" 链接查看用户信息
3. 可以查看邮箱和用户名

### 注销

1. 在首页或 Profile 页面点击 "注销" 按钮
2. 清除登录状态，跳转到登录页面
