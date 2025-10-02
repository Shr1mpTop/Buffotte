"""
Chart Generator Module

Handles generation of visualization charts for market data and predictions.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from datetime import timedelta
from typing import List, Dict, Any


def generate_prediction_chart(predictions: List[Dict[str, Any]], df_recent: pd.DataFrame, output_path: str) -> None:
    """
    Generate a combined chart with:
    1. Last 30 days of candlestick (K-line) chart
    2. Next 5 days predicted prices overlaid

    Args:
        predictions: List of prediction dictionaries with 'day', 'predicted_daily_return', etc.
        df_recent: DataFrame with recent historical data (last 30+ days)
        output_path: Path to save the chart PNG file
    """
    # Get last 30 days of data
    df_plot = df_recent.tail(30).copy()
    df_plot['date'] = pd.to_datetime(df_plot['timestamp'], unit='s')

    # Calculate predicted prices based on the last known close price
    last_close = float(df_plot.iloc[-1]['close_price'])
    last_date = df_plot.iloc[-1]['date']

    pred_dates = []
    pred_prices = [last_close]  # Start with last known price
    current_price = last_close

    for r in predictions:
        # Each prediction is days ahead
        pred_date = last_date + timedelta(days=r['day'])
        pred_dates.append(pred_date)
        # Apply the predicted return to get next price
        current_price = current_price * (1.0 + r['predicted_daily_return'])
        pred_prices.append(current_price)

    # Create figure with larger size
    fig, ax = plt.subplots(figsize=(14, 7))

    # Plot candlesticks for historical data
    prev_close = None
    for idx, row in df_plot.iterrows():
        date = row['date']
        open_p = row['open_price']
        close_p = row['close_price']
        high_p = row['high_price']
        low_p = row['low_price']

        # Determine color: compare today's close with yesterday's close
        # If no previous close (first candle), use open vs close
        if prev_close is None:
            color = 'red' if close_p >= open_p else 'green'
        else:
            color = 'red' if close_p >= prev_close else 'green'

        # Draw high-low line
        ax.plot([date, date], [low_p, high_p], color=color, linewidth=1)

        # Draw open-close box
        height = abs(close_p - open_p)
        bottom = min(open_p, close_p)
        width = timedelta(hours=12)  # Width of candlestick

        rect = Rectangle(
            (mdates.date2num(date) - width.total_seconds()/(2*86400), bottom),
            width.total_seconds()/86400, height,
            facecolor=color, edgecolor=color, alpha=0.8
        )
        ax.add_patch(rect)

        # Update previous close for next iteration
        prev_close = close_p

    # Plot prediction line
    all_pred_dates = [last_date] + pred_dates
    ax.plot(all_pred_dates, pred_prices, 'b--o', linewidth=2, markersize=6,
            label='Predicted Price', alpha=0.7)

    # Add prediction values as text
    for i, (date, price) in enumerate(zip(pred_dates, pred_prices[1:])):
        ax.annotate(f'{price:.2f}', xy=(date, price),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=8, color='blue')

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.xticks(rotation=45)

    # Labels and title
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price', fontsize=12)
    ax.set_title('BUFF Market Trend: Historical K-line + 5-Day Forecast', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close()
