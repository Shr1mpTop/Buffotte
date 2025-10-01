# Buffotte — CS:GO 饰品市场预测项目

这是一个用于 CS:GO 饰品市场（基于 SteamDT 数据）的量化研究与预测仓库。目标是基于历史 Kline 数据构建日级涨幅预测模型，并把模型转化为可回测的交易策略。项目包含数据抓取、特征工程、训练、评估与预测脚本。

核心目录
- `src/kline_crawler.py`：数据抓取（支持历史回溯与增量抓取，timestamp 与 maxTime 单位为秒）。
- `src/train_day_model.py`：Baseline 训练脚本（RandomForest，滞后特征，最近 30 天为验证集）。
- `src/evaluate_model.py`：模型评估（MSE, RMSE, MAE, R2, 方向性准确率）。
- `src/run_daily_report.py`：推荐的一键入口（抓取最新数据、生成预测、绘图并发送 HTML 邮件报告）。
- `models/`：训练或评估生成的模型与 scaler 存放目录（model files 不建议直接 git 提交，除非使用 Git LFS）。

快速开始
1. 安装依赖（建议使用虚拟环境）：
   ```powershell
   ````markdown
   # Buffotte — CS:GO 饰品市场预测项目

   > 该仓库包含数据抓取、特征工程、模型训练、评估与每天自动生成报告并通过邮件发送的脚本。为了简化运维与审阅，已将早期的一些独立脚本归档，仅保留一个统一入口用于日常生产流程。

   核心目录
   - `kline_crawler.py`：数据抓取（支持历史回溯与增量抓取，timestamp 与 maxTime 单位为秒）。
   - `train_day_model.py`：Baseline 训练脚本（RandomForest，滞后特征，最近 30 天为验证集）。
   - `evaluate_model.py`：模型评估（MSE, RMSE, MAE, R2, 方向性准确率）。
   - `run_daily_report.py`：推荐的一键入口（抓取最新数据、生成预测、绘图并发送 HTML 邮件报告）。
   - `models/`：训练或评估生成的模型与 scaler 存放目录（model files 不建议直接 git 提交，除非使用 Git LFS）。

   快速开始
   1. 安装依赖（建议使用虚拟环境）：
      ```powershell
      pip install -r requirements.txt
      ```

   2. 准备数据库配置：在仓库根放置 `config.json`（格式为 pymysql.connect 可接受的 dict），示例：
      ```json
      {
        "host": "127.0.0.1",
        "user": "your_user",
        "password": "your_pass",
        "db": "your_db",
        "charset": "utf8mb4",
        "port": 3306
      }
      ```

   3. 训练 baseline 模型（RandomForest，可选）：
      ```powershell
      python src\train_day_model.py --config .\config.json --val-days 30 --lags 5 --out-dir models
      ```

   4. 评估模型：
      ```powershell
      python src\evaluate_model.py --model models\rf_day_model_*.joblib --scaler models\scaler_day_*.joblib --config .\config.json --val-days 30 --lags 5
      ```

   5. 生成每日市场预测并发送报告（一键推荐）：
      ```powershell
      python src\run_daily_report.py
      ```

   ## 🤖 AI多Agent分析系统（新功能）

   ### 功能概述
   项目新增了基于Google Gemini 2.0的多Agent AI分析系统，模拟证券公司专业分析团队的工作流程：

   - **📊 数据分析师**: 分析历史30天数据，计算技术指标，评估预测准确性
   - **📰 市场分析师**: 搜集市场新闻，分析利好利空因素，评估市场情绪
   - **💼 基金经理**: 综合所有报告，制定投资策略，生成最终建议

   ### 快速开始

   1. **安装AI依赖**：
      ```powershell
      pip install google-generativeai pillow
      ```

   2. **获取Gemini API Key**：
      - 访问 [Google AI Studio](https://aistudio.google.com/)
      - 创建API Key并设置环境变量：
      ```powershell
      $env:GEMINI_API_KEY = "your-api-key-here"
      ```

   3. **运行AI分析**：
      ```powershell
      # AI分析已自动集成到日报告中
      python src\run_daily_report.py
      
      # 或单独测试AI功能
      python test_ai_analysis.py
      ```

   ### 输出报告

   AI分析会生成：
   - **JSON报告**: `models/ai_analysis_report.json` - 结构化分析结果
   - **HTML报告**: `models/ai_analysis_report_*.html` - 精美可视化报告
   - **邮件集成**: 分析摘要和完整报告自动附加到邮件中

   ### 报告示例

   ```
   📊 投资建议: BUY
   信心度: 75%
   市场情绪: positive
   风险等级: medium

   🔍 关键发现：
   • 30日均价上涨12.5%，呈现明确上升趋势
   • 交易量较前期增长35%，市场活跃度提升
   • 预测模型显示未来5天持续看涨信号
   ```

   ### 配置说明

   编辑 `llm_config.json` 自定义AI分析行为：

   ```json
   {
     "llm": {
       "model": "gemini-2.0-flash-exp",
       "temperature": {
         "data_analyst": 0.3,
         "market_analyst": 0.5,
         "fund_manager": 0.4
       }
     },
     "workflow": {
       "enable_news_search": false,
       "save_reports": true,
       "generate_html": true
     }
   }
   ```

   ### 详细文档

   查看 `llm/README.md` 获取：
   - 系统架构详解
   - 每个Agent的职责和prompt设计
   - 自定义开发指南
   - 性能优化建议
   - 故障排除

   存档说明
   - 为简化仓库，若干早期独立脚本（如 `predict.py`, `fetch_only.py`, `send_report.py`, `predict_next_week.py`）已移至 `archive/`。根目录保留小型 stub，指示请使用 `src/run_daily_report.py` 或查看归档脚本。

   注意事项
   - 数据时间单位：所有请求与存储约定为秒（s），避免毫秒混淆。
   - 模型文件通常较大，建议不直接 push 到普通 Git；如需托管，请启用 Git LFS 或把模型上传到 artifact 存储。
   - 训练/评估时请确保 `config.json` 的数据库用户有读取权限。

   下一步建议
   - 若需生产化部署：
     - 把 `config.json` 与 `email_config.json` 中的凭据迁移到环境变量或秘钥管理服务。
     - 把 `src/run_daily_report.py` 注册为 Windows 计划任务或使用 nssm/winsw 安装为服务（详见 `docs/windows_service.md`）。

   打包与安装
   ------------

   本仓库包含一个轻量级 CLI 封装（可选）：

   1. 在开发环境中本地安装（editable）：

   ```powershell
   pip install -e .
   ```

   2. 安装后可使用 `buffotte report`（等价于 `python src/run_daily_report.py`），但最直接的方法是直接运行 `src/run_daily_report.py`。

   3. 若要发布到 PyPI，请完善 `pyproject.toml` 并使用 `twine` 上传。

   注意：安装前请先在虚拟环境中安装依赖（`pip install -r requirements.txt`），并确保 `config.json` 与（可选）`email_config.json` 已配置。

   ````
