"""
Simple Report Builder - Build user-friendly email and HTML reports
"""
from datetime import datetime
from typing import Dict, Any


def build_simple_email_body(analysis_result: Dict[str, Any]) -> str:
    """
    Build simple email body from analysis result.
    
    Args:
        analysis_result: Result from SimpleMarketAnalyzer
        
    Returns:
        Email body text
    """
    report = analysis_result.get('report', '')
    exec_time = analysis_result.get('execution_time', 0)
    
    email_body = f"""{report}

分析耗时: {exec_time:.1f}秒

详细图表请查看附件
"""
    
    return email_body


def build_simple_html_report(analysis_result: Dict[str, Any]) -> str:
    """
    Build simple HTML report from analysis result.
    
    Args:
        analysis_result: Result from SimpleMarketAnalyzer
        
    Returns:
        HTML content
    """
    metrics = analysis_result.get('metrics', {})
    insights = analysis_result.get('insights', {})
    
    price = metrics.get('price', {})
    volume = metrics.get('volume', {})
    sentiment = metrics.get('sentiment', {})
    tech = metrics.get('technical', {})
    
    # Determine color for action
    action = insights.get('action', '观望')
    if action == '买入':
        action_color = '#28a745'
        action_bg = '#d4edda'
    elif action == '卖出':
        action_color = '#dc3545'
        action_bg = '#f8d7da'
    else:
        action_color = '#ffc107'
        action_bg = '#fff3cd'
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BUFF市场日报</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.8;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 8px;
        }}
        .header .date {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .summary {{
            background: {action_bg};
            color: {action_color};
            padding: 25px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            border-bottom: 3px solid {action_color};
        }}
        .section {{
            padding: 25px 30px;
            border-bottom: 1px solid #eee;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section h2 {{
            color: #2a5298;
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #667eea;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            font-size: 16px;
        }}
        .metric .label {{
            color: #666;
        }}
        .metric .value {{
            font-weight: bold;
            color: #333;
        }}
        .action-box {{
            background: {action_bg};
            border-left: 4px solid {action_color};
            padding: 20px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .action-box .action {{
            font-size: 24px;
            font-weight: bold;
            color: {action_color};
            margin-bottom: 10px;
        }}
        .action-box .confidence {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }}
        .action-box .reason {{
            font-size: 16px;
            color: #333;
        }}
        .tips {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
        }}
        .tips ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .tips li {{
            margin: 8px 0;
            color: #555;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            font-size: 13px;
        }}
        .emoji {{
            font-size: 1.3em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 BUFF市场日报</h1>
            <div class="date">{datetime.now().strftime('%Y年%m月%d日')}</div>
        </div>
        
        <div class="summary">
            {insights.get('summary', '市场分析')}
        </div>
        
        <div class="section">
            <h2>📈 价格走势</h2>
            <div class="metric">
                <span class="label">当前价格</span>
                <span class="value">¥{price.get('current', 0)}</span>
            </div>
            <div class="metric">
                <span class="label">20天涨跌</span>
                <span class="value" style="color: {'#28a745' if price.get('change_20d', 0) > 0 else '#dc3545'}">{price.get('change_20d', 0):+.1f}% {price.get('trend_emoji', '')}</span>
            </div>
            <div class="metric">
                <span class="label">历史位置</span>
                <span class="value">{price.get('percentile', 50):.0f}%分位（{'便宜' if price.get('percentile', 50) < 30 else '正常' if price.get('percentile', 50) < 70 else '偏贵'}）</span>
            </div>
        </div>
        
        <div class="section">
            <h2>🔥 市场热度</h2>
            <div class="metric">
                <span class="label">交易热度</span>
                <span class="value">{volume.get('heat_emoji', '')} {volume.get('heat', '正常')}</span>
            </div>
            <div class="metric">
                <span class="label">成交量变化</span>
                <span class="value">比平时{volume.get('change_pct', 0):+.0f}%</span>
            </div>
            <div class="metric">
                <span class="label">市场情绪</span>
                <span class="value">{sentiment.get('emoji', '')} {sentiment.get('level', '中性')} ({sentiment.get('score', 50)}分)</span>
            </div>
        </div>
        
        <div class="section">
            <h2>🎯 操作建议</h2>
            <div class="action-box">
                <div class="action">{action}</div>
                <div class="confidence">信心度: {insights.get('confidence', 50)}%</div>
                <div class="reason">{insights.get('reason', '')}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 技术参考</h2>
            <div class="metric">
                <span class="label">RSI指标</span>
                <span class="value">{tech.get('rsi', 50):.1f} {'（超卖）' if tech.get('rsi', 50) < 30 else '（超买）' if tech.get('rsi', 50) > 70 else '（正常）'}</span>
            </div>
            <div class="metric">
                <span class="label">MACD</span>
                <span class="value">{tech.get('macd_signal', '中性')}</span>
            </div>
            <div class="metric">
                <span class="label">价格趋势</span>
                <span class="value">{price.get('trend_emoji', '')} {price.get('trend', '震荡')}</span>
            </div>
        </div>
        
        <div class="footer">
            <p>本报告基于真实市场数据生成，分析耗时 {analysis_result.get('execution_time', 0):.1f}秒</p>
            <p>仅供参考，不构成投资建议</p>
        </div>
    </div>
</body>
</html>"""
    
    return html
