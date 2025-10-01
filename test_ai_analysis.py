"""
Test script for LLM Multi-Agent Analysis

Usage:
    python test_ai_analysis.py
"""
import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.workflow import AnalysisWorkflow


def generate_sample_data():
    """Generate sample historical data for testing."""
    # Generate 30 days of sample data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    # Simulate price data with trend
    base_price = 100.0
    prices = []
    volumes = []
    
    for i in range(30):
        # Add trend + noise
        trend = i * 0.5
        noise = (hash(str(dates[i])) % 100) / 100 * 2 - 1
        price = base_price + trend + noise
        prices.append(price)
        
        # Volume with some variance
        volume = 10000 + (hash(str(dates[i])) % 5000)
        volumes.append(volume)
    
    df = pd.DataFrame({
        'timestamp': [int(d.timestamp()) for d in dates],
        'open_price': prices,
        'high_price': [p * 1.02 for p in prices],
        'low_price': [p * 0.98 for p in prices],
        'close_price': prices,
        'volume': volumes
    })
    
    return df


def generate_sample_predictions():
    """Generate sample predictions for testing."""
    return [
        {'day': 1, 'predicted_daily_return': 0.005, 'direction': 'up'},
        {'day': 2, 'predicted_daily_return': 0.008, 'direction': 'up'},
        {'day': 3, 'predicted_daily_return': 0.003, 'direction': 'up'},
        {'day': 4, 'predicted_daily_return': -0.002, 'direction': 'down'},
        {'day': 5, 'predicted_daily_return': 0.001, 'direction': 'up'},
    ]


def main():
    print("="*70)
    print("🧪 LLM Multi-Agent Analysis Test")
    print("="*70)
    
    # Try to load API key from config file first
    api_key = None
    config_path = 'llm_config.json'
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            api_key_value = config.get('llm', {}).get('api_key')
            if api_key_value and api_key_value.startswith('AIza'):
                api_key = api_key_value
                print("\n✓ API Key loaded from config file")
        except Exception as e:
            print(f"\nWarning: Failed to load config: {e}")
    
    # Fall back to environment variable
    if not api_key:
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            print("\n✓ API Key found in environment")
    
    # Check if we have an API key
    if not api_key:
        print("\n❌ Error: No API key found")
        print("\nPlease either:")
        print("  1. Add 'api_key' to llm_config.json:")
        print('     "api_key": "AIza..."')
        print("  2. Or set environment variable:")
        print("     Windows: $env:GEMINI_API_KEY = 'your-key-here'")
        print("     Linux/Mac: export GEMINI_API_KEY='your-key-here'")
        return 1
    
    # Generate sample data
    print("\n📊 Generating sample data...")
    df = generate_sample_data()
    predictions = generate_sample_predictions()
    
    print(f"  - Historical data: {len(df)} days")
    print(f"  - Predictions: {len(predictions)} days")
    
    # Create sample chart (placeholder)
    chart_path = 'models/sample_chart.png'
    os.makedirs('models', exist_ok=True)
    
    # Create a simple placeholder chart
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 6))
        plt.plot(df['close_price'].values)
        plt.title('Sample Price Chart')
        plt.xlabel('Days')
        plt.ylabel('Price')
        plt.savefig(chart_path)
        plt.close()
        print(f"  - Chart saved: {chart_path}")
    except Exception as e:
        print(f"  - Warning: Could not create chart: {e}")
        chart_path = None
    
    # Initialize workflow
    print("\n🤖 Initializing AI workflow...")
    try:
        workflow = AnalysisWorkflow(gemini_api_key=api_key, config_path=config_path)
        print("✓ Workflow initialized")
    except Exception as e:
        print(f"❌ Failed to initialize workflow: {e}")
        return 1
    
    # Run analysis
    print("\n🚀 Running multi-agent analysis...")
    print("This may take 30-60 seconds...\n")
    
    try:
        results = workflow.run_full_analysis(
            historical_data=df,
            predictions=predictions,
            chart_path=chart_path,
            enable_news_search=False
        )
        
        print("\n" + "="*70)
        print("✅ Analysis Complete!")
        print("="*70)
        
        # Display summary
        summary = results.get('summary', {})
        print(f"\n📊 ANALYSIS SUMMARY")
        print(f"{'='*70}")
        print(f"Recommendation:     {summary.get('recommendation', 'N/A').upper()}")
        print(f"Confidence:         {summary.get('confidence', 0)*100:.0f}%")
        print(f"Market Sentiment:   {summary.get('market_sentiment', 'N/A')}")
        print(f"Risk Level:         {summary.get('risk_level', 'N/A')}")
        
        print(f"\n🔍 Key Findings:")
        for i, finding in enumerate(summary.get('key_findings', [])[:3], 1):
            print(f"  {i}. {finding}")
        
        # Save results
        print(f"\n💾 Saving results...")
        json_path = workflow.save_results(output_dir='models', filename='test_analysis.json')
        html_path = workflow.generate_html_report(output_dir='models')
        
        print(f"\n📁 Output Files:")
        print(f"  - JSON: {json_path}")
        print(f"  - HTML: {html_path}")
        
        print(f"\n{'='*70}")
        print("🎉 Test completed successfully!")
        print(f"{'='*70}")
        print(f"\nOpen the HTML report to view the full analysis:")
        print(f"  {os.path.abspath(html_path)}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
