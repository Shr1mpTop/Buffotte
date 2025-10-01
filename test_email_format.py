"""
Test email format without actually sending

Tests the email body generation with AI analysis
"""
import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock results
predictions = [
    {'day': 1, 'predicted_daily_return': 0.008, 'direction': 'up'},
    {'day': 2, 'predicted_daily_return': 0.012, 'direction': 'up'},
    {'day': 3, 'predicted_daily_return': -0.003, 'direction': 'down'},
    {'day': 4, 'predicted_daily_return': 0.005, 'direction': 'up'},
    {'day': 5, 'predicted_daily_return': 0.002, 'direction': 'up'},
]

ai_results = {
    'summary': {
        'recommendation': 'buy',
        'confidence': 0.75,
        'market_sentiment': 'positive',
        'risk_level': 'medium',
        'key_findings': [
            '30日均价上涨12.5%，呈现明确上升趋势',
            '交易量较前期增长35%，市场活跃度提升',
            '预测模型显示未来5天持续看涨信号'
        ]
    }
}

def generate_email_preview():
    """Generate email body preview"""
    
    current_date = datetime.now(timezone.utc).astimezone().strftime('%Y年%m月%d日')
    subject = f'BUFF市场分析报告 - {current_date}'
    first = predictions[0]
    
    # Build comprehensive email body
    body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 BUFF饰品市场 AI分析报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
报告日期：{current_date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # Add AI analysis summary
    if ai_results:
        summary = ai_results.get('summary', {})
        recommendation = summary.get('recommendation', 'N/A').upper()
        confidence = summary.get('confidence', 0)*100
        sentiment = summary.get('market_sentiment', 'N/A')
        risk_level = summary.get('risk_level', 'N/A')
        
        # Recommendation emoji
        rec_emoji = {'BUY': '📈', 'SELL': '📉', 'HOLD': '⏸️'}.get(recommendation, '❓')
        
        body += f"""
🤖 【AI多Agent分析结论】（重点关注）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{rec_emoji} 投资建议：{recommendation}
💯 信心度：{confidence:.0f}%
📊 市场情绪：{sentiment.upper()}
⚠️  风险等级：{risk_level.upper()}

🔍 关键发现：
"""
        for i, finding in enumerate(summary.get('key_findings', [])[:3], 1):
            body += f"{i}. {finding}\n"
        
        body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # Add prediction summary
    body += f"""
🔮 【模型预测】未来5天走势

明日预测：{first['direction'].upper()} (预期回报率 {first['predicted_daily_return']*100:.2f}%)

完整5日预测：
"""
    for r in predictions:
        direction_emoji = '🟢' if r['direction'] == 'up' else '🔴' if r['direction'] == 'down' else '⚪'
        body += f"{direction_emoji} 第{r['day']}天: {r['direction'].upper():6s} ({r['predicted_daily_return']*100:+.2f}%)\n"
    
    body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📎 附件说明：
• AI分析完整报告.html (⭐推荐查看)
• 预测K线图.png
• 预测数据.json
• AI分析数据.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  免责声明：
本报告由AI系统自动生成，仅供参考，不构成投资建议。
投资有风险，决策需谨慎。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Powered by Buffotte AI Analysis System
"""

    return subject, body


if __name__ == '__main__':
    print("="*70)
    print("📧 Email Preview")
    print("="*70)
    
    subject, body = generate_email_preview()
    
    print(f"\n主题: {subject}\n")
    print("="*70)
    print("邮件正文:")
    print("="*70)
    print(body)
    print("="*70)
    print("\n✅ 邮件格式预览生成完成")
    print("\n说明：")
    print("- AI分析结论置于最前（重点关注）")
    print("- 包含投资建议、信心度、市场情绪")
    print("- 显示关键发现")
    print("- 附带5日预测详情")
    print("- 所有附件（HTML报告、图表、JSON数据）都会自动附加")
