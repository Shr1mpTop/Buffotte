# 用户数据库和认证系统

## 概述

本项目实现了完整的用户注册、登录和认证系统，包括后端数据库存储、前端用户界面和 API 接口。

## 数据库设计

### user 表结构

```sql
CREATE TABLE user (
    id VARCHAR(255) PRIMARY KEY,           -- 基于邮箱生成的唯一 SHA256 哈希 ID
    username VARCHAR(255) NOT NULL,        -- 用户名
    email VARCHAR(255) UNIQUE NOT NULL,    -- 邮箱地址（唯一）
    password_hash VARCHAR(255) NOT NULL,   -- bcrypt 哈希后的密码
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 创建时间
)
```

### 设计特点

- **唯一 ID 生成**: 使用 `hashlib.sha256(email.encode()).hexdigest()` 根据邮箱生成唯一用户 ID
- **密码安全**: 使用 bcrypt 算法进行密码哈希，提供盐值和多次迭代
- **邮箱唯一性**: 确保每个邮箱只能注册一个账户

## 扩展功能

### 可能的增强

- **密码重置**: 通过邮箱发送重置链接
- **邮箱验证**: 注册时验证邮箱真实性
- **JWT 令牌**: 替换本地存储，使用无状态认证
- **角色权限**: 添加用户角色和权限控制
- **用户资料更新**: 允许用户修改个人信息

### API 扩展

- `GET /api/user/profile` - 获取用户资料
- `PUT /api/user/profile` - 更新用户资料
- `POST /api/user/change-password` - 修改密码

## 故障排除

### 常见问题

1. **CORS 错误**: 检查 FastAPI 的 CORS 配置
2. **数据库连接失败**: 验证 .env 文件和 MySQL 配置
3. **密码验证失败**: 确保 bcrypt 正确安装
4. **前端无法连接后端**: 检查端口和防火墙设置

### 日志查看

- 后端错误日志通过控制台输出
- 前端错误通过浏览器开发者工具查看
- 数据库错误通过 pymysql 异常处理

## 总结

本用户系统实现了完整的注册、登录和认证功能，具有良好的安全性和可扩展性。通过前后端分离的架构，为后续功能扩展提供了坚实的基础。</content>
<parameter name="filePath">e:\github\Buffotte\docs\db\user.md
