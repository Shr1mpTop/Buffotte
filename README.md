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
      ```bash
      python run_daily_report.py
      ```

   ## 🤖 AI市场分析（简洁版）

   ### 功能概述
   项目使用AI提供简洁、易懂的市场分析：

   - **基于真实数据**: 所有指标都是基于历史数据计算，不是AI编造
   - **通俗易懂**: 避免专业术语，像和朋友聊天一样
   - **快速高效**: 10-20秒内完成分析（vs 旧版130秒）
   - **一目了然**: 3秒内看懂核心观点

   ### 快速开始

   1. **安装AI依赖**：
      ```bash
      pip install google-generativeai
      # 或使用豆包
      pip install openai
      ```

   2. **配置API Key**：
      编辑 `llm_config.json`：
      ```json
      {
        "llm": {
          "provider": "google",
          "model": "gemini-2.0-flash-exp",
          "api_key": "your-api-key-here"
        }
      }
      ```

   3. **运行分析**：
      ```bash
      # 使用Gemini（默认）
      python run_daily_report.py
      
      # 使用豆包
      python run_daily_report.py --model doubao
      ```

   ### 报告示例

   ```
   💡 今日结论
   价格处于低位但成交量不足，建议观望等待

   📈 价格走势
   当前价格: ¥1169.57
   最近涨跌: 20天跌了3% ↓
   历史位置: 处于历史20%分位（便宜）

   🔥 市场热度
   交易热度: ❄️ 冷清（成交量比平时少12%）
   市场情绪: 😐 中性 (47分/100分)

   🎯 操作建议
   观望 （信心度: 60%）
   
   什么时候可以考虑买入？
   ✓ 价格继续跌到¥1050以下
   ✓ 成交量放大20%以上
   ✓ 连续3天不再下跌
   ```

   ## 🚀 API服务

   项目提供了FastAPI服务，用于通过HTTP API访问每日报告。

   ### 安装API依赖
   ```bash
   pip install fastapi uvicorn
   ```

   ### 启动API服务器
   ```bash
   python run_api.py
   ```

   服务器将在 `http://localhost:8000` 启动，API文档可在 `http://localhost:8000/docs` 查看。

   ### API端点

   - `GET /` - API根路径
   - `GET /report` - 获取完整的每日报告数据
   - `GET /report/markdown` - 获取报告的Markdown格式内容
   - `GET /report/summary` - 获取报告摘要信息

   ### 部署到生产环境

   对于生产部署，可以使用以下命令：

   ```bash
   uvicorn api:app --host 0.0.0.0 --port 8000
   ```

   或者使用Gunicorn：

   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app
   ```

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
