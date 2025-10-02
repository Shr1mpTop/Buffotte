"""run_daily_report.py

Main orchestrator to be scheduled daily:
1) Fetch latest kline day data and insert into DB
2) Build features from DB, predict tomorrow and next 5 trading days
3) Generate AI analysis report with multi-agent workflow
4) Create visualizations and export to PNG/PDF
5) Send email report with summary and attachments

Usage: python run_daily_report.py

Notes:
- This script expects `config.json` (DB config) and joblib model/scaler files under `models/`
- To enable email sending, configure `email_config.json` with SMTP credentials
"""
import os
import sys
import json
from datetime import datetime, timezone

# Import modular functions
from src.data_fetcher import fetch_and_insert, load_recent_data
from src.feature_engineering import build_features
from src.model_loader import find_model_and_scaler, load_model_and_scaler
from src.predictor import predict_next_days
from src.chart_generator import generate_prediction_chart
from src.email_sender import send_email_report
from src.report_builder import build_markdown_report

# Import AI workflow and report generator
from llm.workflow import AnalysisWorkflow
from llm.report_generator import ReportGenerator

# Configuration constants
MODELS_DIR = 'models'
DB_CONFIG = 'config.json'
EMAIL_CONFIG = 'email_config.json'
LLM_CONFIG = 'llm_config.json'


def main():
    """Main workflow orchestrator."""
    # Step 0: Config and setup
    if not os.path.exists(DB_CONFIG):
        print(f'DB config not found: {DB_CONFIG}')
        return

    current_date_str = datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d')
    print(f"--- Running Daily Report for {current_date_str} ---")

    # Step 1: Fetch and insert latest data
    print("\n[1/6] Fetching latest market data...")
    inserted = fetch_and_insert(DB_CONFIG, days=5)
    print(f"-> Inserted {inserted} new rows.")

    # Step 2: Load recent data and build features
    print("\n[2/6] Loading data and building features...")
    df = load_recent_data(DB_CONFIG, nrows=60)
    df_feat, feat_cols = build_features(df, lags=5)
    print("-> Features built successfully.")

    # Step 3: Load model & scaler
    print("\n[3/6] Loading prediction model and scaler...")
    model_path, scaler_path = find_model_and_scaler(MODELS_DIR)
    if not model_path or not scaler_path:
        print('! Model or scaler not found in models/; aborting prediction.')
        return

    model, scaler = load_model_and_scaler(model_path, scaler_path)
    print(f"-> Model: {os.path.basename(model_path)}")
    print(f"-> Scaler: {os.path.basename(scaler_path)}")

    # Step 4: Predict next 5 days and generate chart
    print("\n[4/6] Generating 5-day market forecast...")
    predictions = predict_next_days(model, scaler, df_feat, feat_cols, days=5)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    # Save predictions to JSON
    out_json_path = os.path.join(MODELS_DIR, 'next_week_prediction.json')
    with open(out_json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': timestamp,
            'predictions': predictions
        }, f, ensure_ascii=False, indent=2)
    print(f"-> Forecast saved to {out_json_path}")

    # Generate prediction chart
    chart_path = os.path.join(MODELS_DIR, f'next_week_prediction_{timestamp}.png')
    generate_prediction_chart(predictions, df, chart_path)
    print(f"-> Forecast chart saved to {chart_path}")

    # Step 5: Run Multi-Agent AI Analysis
    print("\n[5/6] Running Multi-Agent AI Analysis Workflow...")

    # Load LLM config
    try:
        with open(LLM_CONFIG, 'r', encoding='utf-8') as f:
            llm_config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading or parsing {LLM_CONFIG}: {e}", file=sys.stderr)
        return

    # Run AI workflow
    workflow = AnalysisWorkflow(llm_config=llm_config)
    ai_results = workflow.run_full_analysis(
        historical_data=df,
        predictions=predictions,
        chart_path=chart_path,
        enable_news_search=llm_config.get('workflow', {}).get('enable_news_search', False)
    )

    # Build full markdown report with chart
    full_markdown_report = build_markdown_report(ai_results, chart_path)

    # Step 6: Generate Report Files and Cache Email Content
    print("\n[6/6] Generating report files and caching email content...")

    # Generate PNG and PDF from the full markdown report
    report_gen = ReportGenerator(output_dir=MODELS_DIR)
    report_files = report_gen.generate_all(full_markdown_report, "daily_market_report")

    # Use the summary from the summarizer agent as the email body
    email_body = ai_results.get('summary_agent', {}).get('summary', 'AI分析摘要不可用。')

    subject = f"BUFF市场AI分析日报 - {current_date_str}"

    # Prepare attachments: PNG, PDF reports and prediction chart
    attachments = list(report_files.values())
    if os.path.exists(chart_path):
        attachments.append(chart_path)

    # Save email cache for later sending
    email_cache = {
        'generated_at': timestamp,
        'date': current_date_str,
        'subject': subject,
        'body': email_body,
        'attachments': attachments,
        'markdown_report': full_markdown_report,
        'ai_results_summary': {
            'data_analyst': ai_results.get('data_analyst', {}),
            'market_analyst': ai_results.get('market_analyst', {}),
            'fund_manager': ai_results.get('fund_manager', {}),
            'summary_agent': ai_results.get('summary_agent', {})
        }
    }
    
    cache_path = os.path.join(MODELS_DIR, 'email_cache.json')
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(email_cache, f, ensure_ascii=False, indent=2)
    
    print(f"-> Email cache saved to {cache_path}")
    print("-> Report files generated successfully.")
    print(f"\n💡 To send the report via email, run: python send_cached_report.py")

    print(f"\n--- Daily Report for {current_date_str} Finished ---")


if __name__ == '__main__':
    main()
