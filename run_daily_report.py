"""run_daily_report.py

Main orchestrator to be scheduled daily:
1) Fetch latest kline day data and insert into DB
2) Build features from DB, predict tomorrow and next 5 trading days
3) Generate AI analysis report with simple workflow
4) Create visualizations and export to HTML
5) Send email report with summary and attachments

Usage: 
  python run_daily_report.py                           # Use simple workflow (default)
  python run_daily_report.py --model doubao            # Use Doubao LLM instead of Gemini

Notes:
- This script expects `config.json` (DB config) and joblib model/scaler files under `models/`
- To enable email sending, configure `email_config.json` with SMTP credentials
"""
import os
import sys
import json
import argparse
from datetime import datetime, timezone

# Set matplotlib backend before any other imports that might use it
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for thread safety

# Import modular functions
from src.data_fetcher import fetch_and_insert, load_recent_data
from src.feature_engineering import build_features
from src.model_loader import find_model_and_scaler, load_model_and_scaler
from src.predictor import predict_next_days
from src.chart_generator import generate_prediction_chart
from src.github_uploader import upload_prediction_chart

# Import simple AI workflow
from llm.simple_workflow import SimpleMarketAnalyzer
from llm.simple_report_builder import build_simple_email_body, build_simple_html_report

# Configuration constants
MODELS_DIR = 'models'
DB_CONFIG = 'config.json'
EMAIL_CONFIG = 'email_config.json'
LLM_CONFIG = 'llm_config.json'


def main():
    """Main workflow orchestrator."""
    parser = argparse.ArgumentParser(
        description='Run daily market analysis report with simple AI analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Use simple workflow with Gemini (default)
  %(prog)s --model doubao           Use Doubao LLM instead of Gemini
        """
    )
    parser.add_argument('--model', choices=['gemini', 'doubao'], default='gemini',
                       help='LLM model to use (default: gemini)')
    args = parser.parse_args()
    
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

    # Upload chart to GitHub
    print("\n[4.5/6] Uploading prediction chart to GitHub...")
    try:
        with open(DB_CONFIG, 'r', encoding='utf-8') as f:
            db_config = json.load(f)
        github_token = db_config.get('github_token')
        if github_token and github_token != 'your_github_token_here':
            date_str = datetime.now(timezone.utc).strftime('%Y%m%d')
            chart_url = upload_prediction_chart(chart_path, date_str, github_token)
            if chart_url:
                print(f"-> Chart uploaded successfully: {chart_url}")
            else:
                print("-> Chart upload failed, using local path")
                chart_url = chart_path
        else:
            print("-> GitHub token not configured, using local chart path")
            chart_url = chart_path
    except Exception as e:
        print(f"-> Error uploading chart: {e}, using local path")
        chart_url = chart_path

    # Step 5: Run Simple AI Analysis
    print("\n[5/6] Running Simple Market Analysis...")

    # Load LLM config
    try:
        with open(LLM_CONFIG, 'r', encoding='utf-8') as f:
            llm_config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading or parsing {LLM_CONFIG}: {e}", file=sys.stderr)
        return

    # Override LLM provider if specified via command line
    if args.model == 'doubao':
        # Try to get API key from llm_config first, then fallback to DB config
        doubao_api_key = llm_config['llm'].get('doubao_api_key')
        
        if not doubao_api_key or doubao_api_key == 'your_doubao_api_key_here':
            # Fallback: try to read from DB config
            try:
                with open(DB_CONFIG, 'r', encoding='utf-8') as f:
                    db_config = json.load(f)
                doubao_api_key = db_config.get('doubao_api_key')
            except Exception as e:
                print(f"Error loading DB config: {e}")
        
        if not doubao_api_key or doubao_api_key == 'your_doubao_api_key_here':
            print("Error: Doubao API key not configured!")
            print("Please add 'doubao_api_key' to llm_config.json or config.json")
            return
        
        # Override LLM config for Doubao
        llm_config['llm']['provider'] = 'doubao'
        doubao_model = llm_config['llm'].get('doubao_model', 'doubao-seed-1.6-thinking')
        llm_config['llm']['model'] = doubao_model.strip()
        llm_config['llm']['api_key'] = doubao_api_key
        
        print(f"-> Using Doubao LLM: {llm_config['llm']['model']}")
    elif args.model == 'gemini':
        # Ensure Google provider is set
        llm_config['llm']['provider'] = 'google'
        gemini_model = llm_config['llm'].get('model', 'gemini-2.0-flash-exp')
        print(f"-> Using Google Gemini: {gemini_model}")

    # Use simple workflow - fast, clear, easy to understand
    print("-> Using Simple Workflow (快速简洁)")
    analyzer = SimpleMarketAnalyzer(llm_config=llm_config)
    ai_results = analyzer.analyze(
        historical_data=df,
        predictions=predictions,
        chart_path=chart_url
    )
    
    # Build simple report
    full_markdown_report = ai_results.get('report', '')
    email_body = build_simple_email_body(ai_results)
    
    # Build HTML report
    html_content = build_simple_html_report(ai_results)
    html_report_path = os.path.join(MODELS_DIR, f'simple_report_{timestamp}.html')
    with open(html_report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"   -> HTML report generated: {html_report_path}")
    
    # Save analysis result
    analyzer.save_report(ai_results, MODELS_DIR)
    
    exec_times = {'total_time': ai_results.get('execution_time', 0)}
    print(f"   -> Analysis completed in {exec_times['total_time']:.2f}s")

    # Step 6: Generate Report Files and Cache Email Content
    print("\n[6/6] Caching email content...")

    # Prepare attachments
    attachments = []
    
    # Add HTML report
    if os.path.exists(html_report_path):
        attachments.append(html_report_path)
    
    # Add prediction chart
    if os.path.exists(chart_path):
        attachments.append(chart_path)

    subject = f"BUFF市场日报 - {current_date_str}"

    # Save email cache for later sending
    email_cache = {
        'generated_at': timestamp,
        'date': current_date_str,
        'subject': subject,
        'body': email_body,
        'attachments': attachments,
        'markdown_report': full_markdown_report,
        'workflow_type': 'simple',
        'ai_results_summary': ai_results,
        'execution_times': exec_times
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
