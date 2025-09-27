Windows Task Scheduler: 每天自动运行 `run_daily_report.py`

推荐方式（更简洁）：只调度 `run_daily_report.py` 为单个任务在每天的 23:58 运行。

1) 打开 "Task Scheduler" -> Create Basic Task
2) 名称: Buffotte Daily Report
3) Trigger: Daily -> Repeat every 1 day -> Start time: 23:58
4) Action: Start a program
   - Program/script: <path to your python executable, e.g. C:\Anaconda3\envs\buffotte\python.exe>
   - Add arguments: e:\github\Buffotte\run_daily_report.py
   - Start in: e:\github\Buffotte
5) Finish.

说明:
- `run_daily_report.py` 会完成：拉取最新数据、写入 DB、生成预测并发送邮件（若配置了 `email_config.json`）。
- 由于邮件发送需要凭证，请在仓库根目录中创建 `email_config.json`（参照 `email_config.json.template` 填写）。
- 这种一体化的单脚本方案更便于维护和排错（也便于转为服务）。
