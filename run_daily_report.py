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

from kline_crawler import KlineCrawler

MODELS_DIR = 'models'
DB_CONFIG = 'config.json'
EMAIL_CONFIG = 'email_config.json'


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
    plot_and_save(results, out_png)

    # 6) email
    subject = f'Market forecast {datetime.now(timezone.utc).date().isoformat()}'
    first = results[0]
    body = f"Tomorrow prediction: {first['direction']} (expected return {first['predicted_daily_return']:.5f})\n\nFull 5-day:\n"
    for r in results:
        body += f"day {r['day']}: {r['direction']} ({r['predicted_daily_return']:.5f})\n"

    # Create simple HTML body
    inline = [out_png] if os.path.exists(out_png) else []
    html = '<html><body><pre>' + (body.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')) + '</pre>'
    if inline:
        html += '<br><img src="{{INLINE_IMAGE_0}}" alt="chart" />'
    html += '</body></html>'
    send_html_report(EMAIL_CONFIG, subject, html, inline_image_paths=inline, attachments=[out_png, out_json])


if __name__ == '__main__':
    main()
