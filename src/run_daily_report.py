"""run_daily_report.py

Orchestrator to be scheduled daily:
1) At ~23:58 fetch latest kline day data and insert into DB.
2) Build features from DB, predict tomorrow and next 5 trading days.
3) Save JSON and a small visualization under models/.
4) If `email_config.json` exists and contains SMTP credentials, send the report image+summary to the configured recipient.

Usage: python run_daily_report.py

Notes:
- This script expects `config.json` (DB config) and joblib model/scaler files under `models/`.
- To enable email sending, copy `email_config.json.template` -> `email_config.json` and fill SMTP creds.
"""
import os
import json
import time
from datetime import datetime, timezone, timedelta
import joblib
import pandas as pd
import numpy as np
import smtplib
from email.message import EmailMessage
import matplotlib.pyplot as plt

from .kline_crawler import KlineCrawler

MODELS_DIR = 'models'
DB_CONFIG = 'config.json'
EMAIL_CONFIG = 'email_config.json'
LLM_CONFIG = 'llm_config.json'


def fetch_and_insert(db_config_path, days=5):
    """Fetch kline data for the previous `days` days at 23:55 (UTC) and insert into DB.

    Note: we assume the API accepts a timestamp parameter and will return the kline data
    corresponding to that timestamp. We use UTC 23:55 for each day; change if you need
    a different timezone.
    """
    crawler = KlineCrawler(db_config_path=db_config_path)
    total_inserted = 0

    # Read optional automation config from the same config file
    try:
        with open(db_config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}

    force_update = bool(cfg.get('force_update', False))
    history_days = int(cfg.get('history_days', days))

    now_ref = datetime.now(timezone.utc)

    try:
        crawler.connect_db()
        crawler.create_kline_table(ktype='day')

        for d in range(1, history_days + 1):
            target_date = (now_ref - timedelta(days=d)).date()
            # Construct 23:55:10 in Shanghai time (UTC+8), then convert to UTC for API
            shanghai_tz = timezone(timedelta(hours=8))
            target_dt_shanghai = datetime(target_date.year, target_date.month, target_date.day, 23, 55, 10, tzinfo=shanghai_tz)
            # API expects UTC timestamp; convert
            ts = int(target_dt_shanghai.astimezone(timezone.utc).timestamp())
            data = crawler.fetch_recent(timestamp_s=ts)
            # write raw API response to logs for auditing
            try:
                os.makedirs('logs', exist_ok=True)
                log_path = os.path.join('logs', f'fetch_{target_date.isoformat()}_{ts}.json')
                with open(log_path, 'w', encoding='utf-8') as lf:
                    json.dump(data, lf, ensure_ascii=False, indent=2)
            except Exception as e:
                print('Failed to write fetch log:', e)
            rows = KlineCrawler.parse_data_rows(data) if data else []
            if not rows:
                print(f'No rows returned for {target_date.isoformat()} 23:55:10 Shanghai (ts={ts})')
                continue

            # Filter rows to only include those with Shanghai time 23:55:10
            filtered_rows = []
            for r in rows:
                ts_row = int(r[0])
                dt_utc = datetime.fromtimestamp(ts_row, tz=timezone.utc)
                dt_shanghai = dt_utc + timedelta(hours=8)
                if dt_shanghai.hour == 23 and dt_shanghai.minute == 55 and dt_shanghai.second == 10:
                    filtered_rows.append(r)

            if not filtered_rows:
                print(f'No rows with 23:55:10 Shanghai time for {target_date.isoformat()}')
                continue

            if not force_update:
                # Since we filtered to only 23:55:10, we can proceed
                pass

            try:
                inserted = crawler.insert_rows(filtered_rows, ktype='day')
                print(f'Inserted {inserted} rows for {target_date.isoformat()} 23:55:10 Shanghai')
                total_inserted += inserted
            except Exception as e:
                print(f'DB insert failed for {target_date.isoformat()}:', e)
    except Exception as e:
        print('DB operation failed:', e)
    finally:
        try:
            crawler.disconnect_db()
        except Exception:
            pass

    return total_inserted


def find_model_and_scaler():
    # prefer rf baseline if present
    files = os.listdir(MODELS_DIR)
    rf = [f for f in files if f.startswith('rf_day_model') and f.endswith('.joblib')]
    if rf:
        model_path = os.path.join(MODELS_DIR, rf[0])
    else:
        # fallback to lgb fold3
        lg = [f for f in files if f.startswith('lgb_fold3_') and f.endswith('.joblib')]
        model_path = os.path.join(MODELS_DIR, lg[0]) if lg else None
    scaler = [f for f in files if f.startswith('scaler_day') and f.endswith('.joblib')]
    scaler_path = os.path.join(MODELS_DIR, scaler[0]) if scaler else None
    return model_path, scaler_path


def load_recent_df(db_config_path, nrows=60):
    """Load recent kline data.

    Priority for DB connection:
    1. If env var BUFFOTTE_DB_URI is set, use it directly as SQLAlchemy engine URI.
    2. Else fall back to reading `db_config_path` JSON as before.
    """
    # Use SQLAlchemy engine to avoid pandas DBAPI warning and be more compatible
    from sqlalchemy import create_engine

    env_uri = os.getenv('BUFFOTTE_DB_URI')
    if env_uri:
        uri = env_uri
    else:
        with open(db_config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        user = cfg.get('user') or cfg.get('username')
        password = cfg.get('password')
        host = cfg.get('host', '127.0.0.1')
        port = cfg.get('port', 3306)
        db = cfg.get('db') or cfg.get('database')
        charset = cfg.get('charset', 'utf8mb4')
        uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset={charset}"

    engine = create_engine(uri)
    df = pd.read_sql(f'SELECT timestamp, open_price, high_price, low_price, close_price, volume FROM kline_data_day ORDER BY timestamp DESC LIMIT {nrows}', engine)
    df = df.sort_values('timestamp').reset_index(drop=True)
    return df


def featurize(df, lags=5):
    df = df.copy()
    for lag in range(1, lags + 1):
        df[f'close_pct_lag_{lag}'] = df['close_price'].pct_change(periods=lag)
        df[f'vol_lag_{lag}'] = df['volume'].shift(lag)
    feat_cols = []
    for lag in range(1, lags + 1):
        feat_cols += [f'close_pct_lag_{lag}', f'vol_lag_{lag}']
    df = df.dropna().reset_index(drop=True)
    return df, feat_cols


def predict_next_days(model, scaler, df, feat_cols, days=5):
    cur = df.copy()
    # use last fully populated row as base
    cur_row = cur.dropna().iloc[-1:].copy()
    results = []
    for d in range(1, days + 1):
        X = cur_row[feat_cols].values
        Xs = scaler.transform(X)
        pred = float(model.predict(Xs)[0])
        results.append({'day': d, 'predicted_daily_return': pred, 'direction': 'up' if pred > 0 else ('flat' if pred == 0 else 'down')})
        # simulate new row
        today_close = float(cur_row['close_price'].values[0])
        sim_close = today_close * (1.0 + pred)
        sim_volume = float(cur_row['volume'].values[0])
        new = cur_row.copy()
        new['timestamp'] = int(cur_row['timestamp'].values[0]) + 86400
        new['open_price'] = today_close
        new['close_price'] = sim_close
        new['high_price'] = max(today_close, sim_close)
        new['low_price'] = min(today_close, sim_close)
        new['volume'] = sim_volume
        hist = pd.concat([cur, new], ignore_index=True)
        for lag in range(1, 6):
            hist[f'close_pct_lag_{lag}'] = hist['close_price'].pct_change(periods=lag)
            hist[f'vol_lag_{lag}'] = hist['volume'].shift(lag)
        cur = hist.copy()
        cur_row = cur.dropna().iloc[-1:].copy()
    return results


def plot_and_save(df, results, out_png):
    import matplotlib.dates as mdates
    from mplfinance.original_flavor import candlestick_ohlc

    # Get last 30 days
    df_plot = df.tail(30).copy()
    df_plot['Date'] = pd.to_datetime(df_plot['timestamp'], unit='s')
    df_plot.set_index('Date', inplace=True)

    # Prepare data for candlestick: [(date, open, high, low, close), ...]
    quotes = []
    for idx, row in df_plot.iterrows():
        quotes.append((mdates.date2num(idx), row['open_price'], row['high_price'], row['low_price'], row['close_price']))

    # Generate future data
    last_row = df_plot.iloc[-1]
    future_quotes = []
    current_close = last_row['close_price']
    last_date = df_plot.index[-1]
    for i, r in enumerate(results):
        pred_return = r['predicted_daily_return']
        new_close = current_close * (1 + pred_return)
        new_open = current_close
        new_high = max(new_open, new_close)
        new_low = min(new_open, new_close)
        future_date = last_date + pd.Timedelta(days=i+1)
        future_quotes.append((mdates.date2num(future_date), new_open, new_high, new_low, new_close))
        current_close = new_close

    fig, ax = plt.subplots(figsize=(12, 8))

    # Prepare data for candlestick
    quotes = []
    prev_close = None
    for idx, row in df_plot.iterrows():
        quotes.append((mdates.date2num(idx), row['open_price'], row['high_price'], row['low_price'], row['close_price'], prev_close))
        prev_close = row['close_price']

    # Plot historical candlesticks with colors based on close > prev_close
    for q in quotes:
        date, open_p, high, low, close, prev_c = q
        if prev_c is not None:
            body_color = 'r' if close > prev_c else 'g'
        else:
            body_color = 'b'  # first day
        wick_color = 'black'  # wick always black
        # Draw wick: lower shadow and upper shadow
        body_low = min(open_p, close)
        body_high = max(open_p, close)
        ax.plot([date, date], [low, body_low], color=wick_color, linewidth=1)  # lower shadow
        ax.plot([date, date], [body_high, high], color=wick_color, linewidth=1)  # upper shadow
        # Draw body
        body_bottom = body_low
        body_height = body_high - body_low
        ax.bar(date, body_height, width=0.6, bottom=body_bottom, color=body_color, alpha=0.8)

    # Plot future as dashed candlesticks
    for i in range(len(future_quotes)):
        date, open_p, high, low, close = future_quotes[i]
        body_low = min(open_p, close)
        body_high = max(open_p, close)
        # Draw wick
        ax.plot([date, date], [low, body_low], color='gray', linestyle='--', linewidth=1)  # lower shadow
        ax.plot([date, date], [body_high, high], color='gray', linestyle='--', linewidth=1)  # upper shadow
        # Draw body
        body_bottom = body_low
        body_height = body_high - body_low
        ax.bar(date, body_height, width=0.6, bottom=body_bottom, color='blue', alpha=0.5)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    plt.xticks(rotation=45)
    ax.set_title('Market Candlestick Chart with 7-Day Prediction')
    ax.set_ylabel('Price')
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()


def build_integrated_email(ai_results, predictions, chart_path, current_date):
    """
    Build integrated HTML email with complete AI report embedded and chart inlined.
    
    Args:
        ai_results: AI analysis results dict
        predictions: Model predictions list
        chart_path: Path to prediction chart PNG
        current_date: Current date string
    
    Returns:
        Complete HTML string for email body
    """
    # Extract AI report components
    data_result = ai_results.get('data_analyst', {}) if ai_results else {}
    market_result = ai_results.get('market_analyst', {}) if ai_results else {}
    manager_result = ai_results.get('fund_manager', {}) if ai_results else {}
    summary = ai_results.get('summary', {}) if ai_results else {}
    
    recommendation = summary.get('recommendation', 'HOLD').upper()
    confidence = summary.get('confidence', 0) * 100
    sentiment = summary.get('market_sentiment', 'N/A')
    risk_level = summary.get('risk_level', 'N/A')
    
    # Recommendation color
    rec_color = {
        'BUY': '#28a745',
        'SELL': '#dc3545',
        'HOLD': '#ffc107'
    }.get(recommendation, '#6c757d')
    
    # Build predictions table HTML
    predictions_html = ""
    for r in predictions:
        direction_emoji = '🟢' if r['direction'] == 'up' else '🔴' if r['direction'] == 'down' else '⚪'
        predictions_html += f"""
        <tr>
            <td>{direction_emoji} 第{r['day']}天</td>
            <td style="color: {'#28a745' if r['direction'] == 'up' else '#dc3545'}; font-weight: bold;">
                {r['direction'].upper()}
            </td>
            <td>{r['predicted_daily_return']*100:+.2f}%</td>
        </tr>
        """
    
    # Build key findings list
    key_findings_html = ""
    for finding in summary.get('key_findings', [])[:5]:
        key_findings_html += f"<li>{finding}</li>"
    
    # Complete HTML email
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BUFF饰品市场AI分析报告 - {current_date}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0;
            background-color: #f5f7fa;
        }}
        .container {{
            background-color: white;
            margin: 20px auto;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 36px;
            font-weight: 700;
        }}
        .header .timestamp {{
            opacity: 0.95;
            font-size: 16px;
            margin-top: 10px;
        }}
        .recommendation-box {{
            background: linear-gradient(135deg, {rec_color}22 0%, {rec_color}11 100%);
            padding: 30px;
            margin: 30px;
            border-radius: 10px;
            border-left: 5px solid {rec_color};
            text-align: center;
        }}
        .recommendation-box h2 {{
            margin: 0 0 20px 0;
            color: #333;
            font-size: 24px;
        }}
        .recommendation {{
            font-size: 56px;
            font-weight: 900;
            color: {rec_color};
            margin: 20px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}
        .confidence {{
            font-size: 28px;
            color: #555;
            font-weight: 600;
        }}
        .metrics {{
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .metric {{
            text-align: center;
            padding: 15px;
            flex: 1;
            min-width: 150px;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }}
        .section {{
            padding: 30px;
            margin: 0;
            border-bottom: 1px solid #eee;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 12px;
            margin-top: 0;
            font-size: 28px;
        }}
        .agent-badge {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        .badge-data {{
            background-color: #e3f2fd;
            color: #1976d2;
        }}
        .badge-market {{
            background-color: #f3e5f5;
            color: #7b1fa2;
        }}
        .badge-manager {{
            background-color: #e8f5e9;
            color: #388e3c;
        }}
        .key-findings {{
            background-color: #fff9e6;
            border-left: 5px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .key-findings h3 {{
            margin-top: 0;
            color: #f57c00;
        }}
        .key-findings ul {{
            margin: 10px 0;
            padding-left: 25px;
        }}
        .key-findings li {{
            margin: 8px 0;
            color: #555;
        }}
        .report-content {{
            white-space: pre-wrap;
            line-height: 1.9;
            color: #444;
            font-size: 15px;
            background-color: #fafafa;
            padding: 20px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .chart-container {{
            margin: 30px 0;
            text-align: center;
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }}
        .predictions-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .predictions-table th {{
            background-color: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        .predictions-table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        .predictions-table tr:hover {{
            background-color: #f8f9fa;
        }}
        .footer {{
            background-color: #2c3e50;
            color: white;
            text-align: center;
            padding: 30px;
            font-size: 14px;
        }}
        .footer p {{
            margin: 8px 0;
            opacity: 0.9;
        }}
        .highlight-box {{
            background: linear-gradient(135deg, #667eea11 0%, #764ba211 100%);
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 BUFF饰品市场AI分析报告</h1>
            <div class="timestamp">📅 生成时间: {current_date}</div>
        </div>
        
        <div class="recommendation-box">
            <h2>🎯 核心投资建议</h2>
            <div class="recommendation">{recommendation}</div>
            <div class="confidence">信心度: {confidence:.0f}%</div>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">市场情绪</div>
                    <div class="metric-value">{sentiment.upper()}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">风险等级</div>
                    <div class="metric-value">{risk_level.upper()}</div>
                </div>
            </div>
        </div>
"""
    
    # Add key findings if available
    if key_findings_html:
        html += f"""
        <div class="section">
            <div class="key-findings">
                <h3>🔍 关键发现（重点关注）</h3>
                <ul>
                    {key_findings_html}
                </ul>
            </div>
        </div>
"""
    
    # Add Fund Manager report
    if manager_result:
        html += f"""
        <div class="section">
            <span class="agent-badge badge-manager">💼 基金经理分析</span>
            <h2>最终投资策略建议</h2>
            <div class="report-content">{manager_result.get('report', '报告生成中...')}</div>
        </div>
"""
    
    # Add prediction chart
    html += f"""
        <div class="section">
            <h2>📈 预测K线图与未来走势</h2>
            <div class="chart-container">
                <img src="{{{{INLINE_IMAGE_0}}}}" alt="预测K线图" />
            </div>
            
            <div class="highlight-box">
                <h3 style="margin-top: 0;">🔮 模型预测 - 未来5日走势</h3>
                <table class="predictions-table">
                    <thead>
                        <tr>
                            <th>交易日</th>
                            <th>预测方向</th>
                            <th>预期回报率</th>
                        </tr>
                    </thead>
                    <tbody>
                        {predictions_html}
                    </tbody>
                </table>
            </div>
        </div>
"""
    
    # Add Data Analyst report
    if data_result:
        html += f"""
        <div class="section">
            <span class="agent-badge badge-data">📊 数据分析师</span>
            <h2>量化数据分析</h2>
            <div class="report-content">{data_result.get('report', '报告生成中...')}</div>
        </div>
"""
    
    # Add Market Analyst report
    if market_result:
        html += f"""
        <div class="section">
            <span class="agent-badge badge-market">📰 市场分析师</span>
            <h2>市场动态与情绪分析</h2>
            <div class="report-content">{market_result.get('report', '报告生成中...')}</div>
        </div>
"""
    
    # Add footer
    html += f"""
        <div class="footer">
            <p><strong>⚠️ 免责声明</strong></p>
            <p>本报告由AI多Agent系统自动生成，基于历史数据分析和机器学习模型预测</p>
            <p>仅供参考，不构成任何投资建议 | 投资有风险，决策需谨慎</p>
            <p style="margin-top: 20px; opacity: 0.7;">Powered by Buffotte AI Analysis System | Gemini 2.0</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def send_html_report(email_cfg_path, subject, html_body, inline_image_paths=None, attachments=None):
    """Send an HTML email. Images in inline_image_paths will be embedded as data URLs in the HTML.
    html_body should already reference images as <img src="cid:..."> or data URIs. For simplicity we will convert first image to base64 and expose as {{INLINE_IMAGE_0}} placeholder.
    """
    # first try environment variables (preferred for security)
    env_cfg = {}
    env_cfg['smtp_server'] = os.getenv('BUFFOTTE_SMTP_SERVER')
    env_cfg['smtp_port'] = os.getenv('BUFFOTTE_SMTP_PORT')
    env_cfg['username'] = os.getenv('BUFFOTTE_SMTP_USERNAME')
    env_cfg['password'] = os.getenv('BUFFOTTE_SMTP_PASSWORD')
    env_cfg['from_address'] = os.getenv('BUFFOTTE_FROM_ADDRESS')
    env_cfg['to_address'] = os.getenv('BUFFOTTE_TO_ADDRESS')
    env_cfg['use_tls'] = os.getenv('BUFFOTTE_SMTP_USE_TLS', 'true').lower() in ('1', 'true', 'yes')

    if all(env_cfg.get(k) for k in ['smtp_server', 'smtp_port', 'username', 'password', 'from_address', 'to_address']):
        cfg = env_cfg
    else:
        # try explicit config file first
        if os.path.exists(email_cfg_path):
            with open(email_cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        else:
            print('Email config not found and env vars not set; skipping email send')
            return False
        required = ['smtp_server', 'smtp_port', 'username', 'password', 'from_address', 'to_address']
        if not all(k in cfg for k in required):
            print('Email config missing required fields and env vars not set; skipping email send')
            return False

    # embed first inline image(s) as data URIs
    html = html_body
    inline_image_paths = inline_image_paths or []
    import base64
    for idx, path in enumerate(inline_image_paths):
        try:
            with open(path, 'rb') as f:
                b = f.read()
            data64 = base64.b64encode(b).decode('ascii')
            mime = 'image/png'
            placeholder = f'{{{{INLINE_IMAGE_{idx}}}}}'
            datauri = f'data:{mime};base64,{data64}'
            html = html.replace(placeholder, datauri)
        except Exception as e:
            print('Failed to inline image', path, e)

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = cfg['from_address']
    msg['To'] = cfg['to_address']
    msg.set_content('This is an HTML email. If you see this, your client does not support HTML.')
    msg.add_alternative(html, subtype='html')

    attachments = attachments or []
    for path in attachments:
        try:
            with open(path, 'rb') as f:
                data = f.read()
            maintype = 'application'
            subtype = 'octet-stream'
            if path.lower().endswith('.png'):
                maintype = 'image'; subtype = 'png'
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=os.path.basename(path))
        except Exception as e:
            print('Failed attach', path, e)

    try:
        server = smtplib.SMTP(cfg['smtp_server'], int(cfg['smtp_port']), timeout=20)
        if cfg.get('use_tls', True):
            server.starttls()
        server.login(cfg['username'], cfg['password'])
        server.send_message(msg)
        server.quit()
        print('Email sent to', cfg['to_address'])
        return True
    except Exception as e:
        print('Email send failed:', e)
        return False


def run_ai_analysis(df, predictions, chart_path):
    """
    Run AI multi-agent analysis workflow.
    
    Returns tuple: (ai_results, html_report_path, json_report_path) or (None, None, None) if disabled
    """
    # Check if LLM config exists and AI analysis is enabled
    if not os.path.exists(LLM_CONFIG):
        print('LLM config not found, skipping AI analysis')
        return None, None, None
    
    try:
        with open(LLM_CONFIG, 'r', encoding='utf-8') as f:
            llm_cfg = json.load(f)
    except Exception as e:
        print(f'Failed to load LLM config: {e}')
        return None, None, None
    
    # Get API key from config or environment
    api_key = None
    llm_config = llm_cfg.get('llm', {})
    
    # Try direct key in config
    api_key_value = llm_config.get('api_key')
    if api_key_value:
        if api_key_value.startswith('AIza'):
            api_key = api_key_value
        else:
            # Treat as environment variable name
            api_key = os.getenv(api_key_value)
    
    # Fall back to GEMINI_API_KEY env var
    if not api_key:
        api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print('Warning: No Gemini API key found in config or environment, skipping AI analysis')
        return None, None, None
    
    try:
        # Import workflow (lazy import to avoid errors if dependencies missing)
        from llm.workflow import AnalysisWorkflow
        
        # Initialize workflow with config
        workflow = AnalysisWorkflow(gemini_api_key=api_key, config_path=LLM_CONFIG)
        
        # Run analysis
        enable_news = llm_cfg.get('workflow', {}).get('enable_news_search', False)
        ai_results = workflow.run_full_analysis(
            historical_data=df.tail(30).copy(),
            predictions=predictions,
            chart_path=chart_path,
            enable_news_search=enable_news
        )
        
        # Save results
        output_dir = llm_cfg.get('workflow', {}).get('output_dir', MODELS_DIR)
        json_path = workflow.save_results(output_dir=output_dir)
        
        # Generate HTML report if enabled
        html_path = None
        if llm_cfg.get('workflow', {}).get('generate_html', True):
            html_path = workflow.generate_html_report(output_dir=output_dir)
        
        return ai_results, html_path, json_path
        
    except ImportError as e:
        print(f'AI analysis dependencies not installed: {e}')
        print('Install with: pip install google-generativeai pillow')
        return None, None, None
    except Exception as e:
        print(f'AI analysis failed: {e}')
        import traceback
        traceback.print_exc()
        return None, None, None


def main():
    # 1) fetch and insert latest data
    if not os.path.exists(DB_CONFIG):
        print('DB config not found:', DB_CONFIG)
        return
    inserted = fetch_and_insert(DB_CONFIG, days=5)
    print('Inserted rows:', inserted)

    # 2) load recent df and featurize
    df = load_recent_df(DB_CONFIG, nrows=60)
    df_feat, feat_cols = featurize(df, lags=5)

    # 3) load model & scaler
    model_path, scaler_path = find_model_and_scaler()
    if not model_path or not scaler_path:
        print('Model or scaler not found in models/; aborting prediction')
        return
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    # 4) predict next 5 days
    results = predict_next_days(model, scaler, df_feat, feat_cols, days=5)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out_json = os.path.join(MODELS_DIR, 'next_week_prediction.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({'generated_at': timestamp, 'predictions': results}, f, ensure_ascii=False, indent=2)

    # 5) plot
    out_png = os.path.join(MODELS_DIR, f'next_week_prediction_{timestamp}.png')
    plot_and_save(df, results, out_png)

    # 6) Run AI analysis
    print('\n' + '='*60)
    print('🤖 Starting AI Multi-Agent Analysis...')
    print('='*60)
    ai_results, ai_html_path, ai_json_path = run_ai_analysis(df, results, out_png)
    
    # 7) Prepare integrated email with embedded AI report
    current_date = datetime.now(timezone.utc).astimezone().strftime('%Y年%m月%d日')
    subject = f'BUFF市场分析报告 - {current_date}'
    
    # Build integrated HTML email with complete AI report embedded
    html = build_integrated_email(ai_results, results, out_png, current_date)
    
    # Inline the chart image
    inline = [out_png] if os.path.exists(out_png) else []
    
    # Attachments: only JSON files for data reference
    attachments = [out_json]
    if ai_json_path and os.path.exists(ai_json_path):
        attachments.append(ai_json_path)
    
    # 8) Send email
    send_html_report(EMAIL_CONFIG, subject, html, inline_image_paths=inline, attachments=attachments)


if __name__ == '__main__':
    main()
