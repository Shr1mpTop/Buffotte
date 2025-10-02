"""
Report Builder Module

Handles building markdown reports from AI analysis results.
"""
from datetime import datetime, timezone
from typing import Dict, Any


def build_markdown_report(ai_results: Dict[str, Any], chart_path: str = None) -> str:
    """
    Combine all agent reports into a single markdown document.

    Args:
        ai_results: Dictionary containing results from all AI agents
        chart_path: Path to the prediction chart image (optional)

    Returns:
        Complete markdown report as a string
    """
    # Safely get reports from the results dictionary
    fund_manager_report = ai_results.get('fund_manager', {}).get('report', '基金经理报告不可用。')
    data_analyst_report = ai_results.get('data_analyst', {}).get('report', '数据分析报告不可用。')
    market_analyst_report = ai_results.get('market_analyst', {}).get('report', '市场分析报告不可用。')

    # Build chart section if chart path provided
    chart_section = ""
    if chart_path:
        import os
        chart_filename = os.path.basename(chart_path)
        chart_section = f"\n![Market Forecast]({chart_filename})\n"

    return f"""
# BUFF饰品市场AI分析报告
**生成时间:** {datetime.now(timezone.utc).astimezone().strftime('%Y年%m月%d日 %H:%M:%S')}
{chart_section}
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
