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
import sys
import json
import time
from datetime import datetime, timezone, timedelta
import joblib
import pandas as pd
import numpy as np
import smtplib
from email.message import EmailMessage
import matplotlib.pyplot as plt

from src.kline_crawler import KlineCrawler
from llm.workflow import AnalysisWorkflow
from llm.report_generator import ReportGenerator

MODELS_DIR = 'models'
DB_CONFIG = 'config.json'
EMAIL_CONFIG = 'email_config.json'
AI_REPORT_PATH = os.path.join(MODELS_DIR, 'ai_analysis_report.json')


def build_full_markdown_report(ai_results: dict) -> str:
    """Combines all agent reports into a single markdown document."""
    
    # Safely get reports from the results dictionary
    fund_manager_report = ai_results.get('fund_manager', {}).get('report', '基金经理报告不可用。')
    data_analyst_report = ai_results.get('data_analyst', {}).get('report', '数据分析报告不可用。')
    market_analyst_report = ai_results.get('market_analyst', {}).get('report', '市场分析报告不可用。')

    return f"""
# BUFF饰品市场AI分析报告
**生成时间:** {datetime.now(timezone.utc).astimezone().strftime('%Y年%m月%d日 %H:%M:%S')}

---

## 🎯 最终投资策略建议
{fund_manager_report}

---

## 📊 数据分析报告
{data_analyst_report}

---

## 📰 市场分析报告
{market_analyst_report}
"""


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


def plot_and_save(results, out_png):
    days = [r['day'] for r in results]
    vals = [r['predicted_daily_return'] for r in results]
    dirs = [r['direction'] for r in results]
    plt.figure(figsize=(8,4))
    cols = ['green' if v>0 else 'red' if v<0 else 'gray' for v in vals]
    plt.bar(days, vals, color=cols)
    plt.axhline(0, color='k', linewidth=0.6)
    plt.xlabel('day')
    plt.ylabel('predicted daily return')
    plt.title('Next days predicted daily returns')
    plt.grid(True, axis='y')
    plt.savefig(out_png)
    plt.close()


def send_report(email_cfg_path, subject, body, attachments=None):
    """Sends an email with attachments."""
    # first try environment variables (preferred for security)
    env_cfg = {
        'smtp_server': os.getenv('BUFFOTTE_SMTP_SERVER'),
        'smtp_port': os.getenv('BUFFOTTE_SMTP_PORT'),
        'username': os.getenv('BUFFOTTE_SMTP_USERNAME'),
        'password': os.getenv('BUFFOTTE_SMTP_PASSWORD'),
        'from_address': os.getenv('BUFFOTTE_FROM_ADDRESS'),
        'to_address': os.getenv('BUFFOTTE_TO_ADDRESS'),
        'use_tls': os.getenv('BUFFOTTE_SMTP_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
    }

    if all(env_cfg.values()):
        cfg = env_cfg
    else:
        if not os.path.exists(email_cfg_path):
            print('Email config not found and env vars not set; skipping email send.')
            return False
        with open(email_cfg_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        
        required = ['smtp_server', 'smtp_port', 'username', 'password', 'from_address', 'to_address']
        if not all(k in cfg for k in required):
            print('Email config missing required fields and env vars not set; skipping email send.')
            return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = cfg['from_address']
    msg['To'] = cfg['to_address']
    msg.set_content(body)

    for path in attachments or []:
        if not os.path.exists(path):
            print(f"Attachment not found, skipping: {path}")
            continue
        try:
            with open(path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(path)
            
            maintype, subtype = 'application', 'octet-stream'
            if file_name.lower().endswith('.png'):
                maintype, subtype = 'image', 'png'
            elif file_name.lower().endswith('.pdf'):
                maintype, subtype = 'application', 'pdf'
            
            msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)
        except Exception as e:
            print(f'Failed to attach file {path}: {e}')

    try:
        server = smtplib.SMTP(cfg['smtp_server'], int(cfg['smtp_port']), timeout=30)
        if cfg.get('use_tls', True):
            server.starttls()
        server.login(cfg['username'], cfg['password'])
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {cfg['to_address']}")
        return True
    except Exception as e:
        print(f'Email send failed: {e}')
        return False


def main():
    # 0) Config and setup
    if not os.path.exists(DB_CONFIG):
        print('DB config not found:', DB_CONFIG)
        return
    
    current_date_str = datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d')
    print(f"--- Running Daily Report for {current_date_str} ---")

    # 1) Fetch and insert latest data
    print("\n[1/6] Fetching latest market data...")
    inserted = fetch_and_insert(DB_CONFIG, days=5)
    print(f"-> Inserted {inserted} new rows.")

    # 2) Load recent df and featurize
    print("\n[2/6] Loading data and building features...")
    df = load_recent_df(DB_CONFIG, nrows=60)
    df_feat, feat_cols = featurize(df, lags=5)
    print("-> Features built successfully.")

    # 3) Load model & scaler
    print("\n[3/6] Loading prediction model and scaler...")
    model_path, scaler_path = find_model_and_scaler()
    if not model_path or not scaler_path:
        print('! Model or scaler not found in models/; aborting prediction.')
        return
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    print(f"-> Model: {os.path.basename(model_path)}")
    print(f"-> Scaler: {os.path.basename(scaler_path)}")

    # 4) Predict next 5 days and generate chart
    print("\n[4/6] Generating 5-day market forecast...")
    predictions = predict_next_days(model, scaler, df_feat, feat_cols, days=5)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    
    out_json_path = os.path.join(MODELS_DIR, 'next_week_prediction.json')
    with open(out_json_path, 'w', encoding='utf-8') as f:
        json.dump({'generated_at': timestamp, 'predictions': predictions}, f, ensure_ascii=False, indent=2)
    print(f"-> Forecast saved to {out_json_path}")

    chart_path = os.path.join(MODELS_DIR, f'next_week_prediction_{timestamp}.png')
    plot_and_save(predictions, chart_path)
    print(f"-> Forecast chart saved to {chart_path}")

    # 5) Run Multi-Agent AI Analysis
    print("\n[5/6] Running Multi-Agent AI Analysis Workflow...")
    
    # Load the entire LLM config from the JSON file
    try:
        with open('llm_config.json', 'r', encoding='utf-8') as f:
            llm_config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading or parsing llm_config.json: {e}", file=sys.stderr)
        return

    # Pass the whole config dictionary to the workflow
    workflow = AnalysisWorkflow(llm_config=llm_config)
    
    ai_results = workflow.run_full_analysis(
        historical_data=df,
        predictions=predictions,
        chart_path=chart_path,
        enable_news_search=llm_config.get('workflow', {}).get('enable_news_search', False)
    )
    
    # Combine all agent reports into one markdown document
    full_markdown_report = build_full_markdown_report(ai_results)
    
    # 6) Generate and Send Email Report
    print("\n[6/6] Generating and sending email report...")
    
    # Generate PNG and PDF from the full markdown report
    report_gen = ReportGenerator(output_dir=MODELS_DIR)
    report_files = report_gen.generate_all(full_markdown_report, "daily_market_report")
    
    # Use the summary from the summarizer agent as the email body
    email_body = ai_results.get('summary_agent', {}).get('summary', 'AI分析摘要不可用。')
    
    subject = f"BUFF市场AI分析日报 - {current_date_str}"

    # Attach the generated PNG and PDF files
    attachments = list(report_files.values())
    
    # Also attach the prediction chart
    if os.path.exists(chart_path):
        attachments.append(chart_path)

    send_status = send_report(
        email_cfg_path=EMAIL_CONFIG,
        subject=subject,
        body=email_body,
        attachments=attachments
    )
    
    if send_status:
        print("-> Email report sent successfully.")
    else:
        print("! Failed to send email report.")
        
    print(f"\n--- Daily Report for {current_date_str} Finished ---")


if __name__ == '__main__':
    main()
