# 前端样式管理说明

## CSS 文件组织结构

前端样式已统一管理在 `src/css/` 文件夹中：

```
src/css/
├── index.css          # 统一导入文件
├── ItemDetail.css     # ItemDetail.vue 组件样式
├── SearchBox.css      # SearchBox.vue 组件样式
└── PriceChart.css     # PriceChart.vue 组件样式
```

## 修改内容

1. **创建了独立的CSS文件**：
   - 将所有Vue组件中的内联 `<style scoped>` 样式提取到独立CSS文件中
   - 保持原有的样式规则和选择器不变

2. **统一导入管理**：
   - 在 `src/css/index.css` 中统一导入所有组件样式
   - 在 `src/main.js` 中导入 `index.css` 文件

3. **组件修改**：
   - 移除了所有组件中的 `<style scoped>` 标签
   - 在组件的 `<script>` 部分导入对应的CSS文件

## 优势

- **更好的代码组织**：样式与组件逻辑分离，便于维护
- **样式复用**：可以在多个组件间共享样式
- **开发效率**：可以单独编辑样式文件，无需在Vue文件中切换
- **版本控制**：样式文件的变更历史更清晰

## 使用方法

如需修改某个组件的样式，请直接编辑对应的CSS文件：

- `ItemDetail.vue` 的样式 → 编辑 `src/css/ItemDetail.css`
- `SearchBox.vue` 的样式 → 编辑 `src/css/SearchBox.css`
- `PriceChart.vue` 的样式 → 编辑 `src/css/PriceChart.css`

新增组件时，请按照以下步骤：

1. 在 `src/css/` 下创建对应的CSS文件
2. 在 `src/css/index.css` 中添加导入语句
3. 在组件的 `<script>` 中导入CSS文件