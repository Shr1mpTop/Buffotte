"""
Report Builder Module

Handles building markdown reports from AI analysis results.
"""
from datetime import datetime, timezone
from typing import Dict, Any


def build_markdown_report(ai_results: Dict[str, Any], chart_path: str = None) -> str:
    """
    Combine all agent reports into a single markdown document.
    Supports both old workflow (v1.0) and new optimized workflow (v2.0) results.

    Args:
        ai_results: Dictionary containing results from all AI agents
        chart_path: Path to the prediction chart image (optional)

    Returns:
        Complete markdown report as a string
    """
    # Check workflow version
    workflow_version = ai_results.get('workflow_version', '1.0')
    
    # Build chart section if chart path provided
    chart_section = ""
    if chart_path:
        import os
        chart_filename = os.path.basename(chart_path)
        chart_section = f"\n![Market Forecast]({chart_filename})\n"
    
    # Handle new optimized workflow (v2.0)
    if workflow_version == '2.0-optimized' or 'strategy_manager' in ai_results:
        # Get executive summary
        exec_summary = ai_results.get('executive_summary', {})
        exec_times = ai_results.get('execution_times', {})
        
        # Get agent reports
        risk_control_report = ai_results.get('risk_control', {}).get('report', '风控报告不可用。')
        strategy_report = ai_results.get('strategy_manager', {}).get('report', '策略报告不可用。')
        quant_report = ai_results.get('quant_researcher', {}).get('report', '量化分析报告不可用。')
        fundamental_report = ai_results.get('fundamental_analyst', {}).get('report', '基本面分析报告不可用。')
        sentiment_report = ai_results.get('sentiment_analyst', {}).get('report', '情绪分析报告不可用。')
        
        return f"""
# BUFF饰品市场AI分析报告 (优化版 v2.0)
**生成时间:** {datetime.now(timezone.utc).astimezone().strftime('%Y年%m月%d日 %H:%M:%S')}  
**分析模式:** 多Agent并发优化  
**总耗时:** {exec_times.get('total_time', 0):.2f}秒 | **性能提升:** {exec_times.get('speedup_estimate', 'N/A')}
{chart_section}
---

## 📊 执行摘要

**交易建议:** {exec_summary.get('trading_action', 'N/A')}  
**策略类型:** {exec_summary.get('strategy_type', 'N/A')}  
**信心度:** {exec_summary.get('confidence', 0)*100:.0f}%  
**建议仓位:** {exec_summary.get('position_size', 0)*100:.0f}%  
**风控审核:** {exec_summary.get('risk_approval', 'N/A')}  
**风险等级:** {exec_summary.get('risk_level', 'N/A')}  

**最终建议:** {exec_summary.get('key_recommendation', 'N/A')}

---

## 🛡️ 风险控制审核报告
{risk_control_report}

---

## 📋 交易策略报告
{strategy_report}

---

## 🔬 量化分析报告
{quant_report}

---

## 📊 基本面分析报告
{fundamental_report}

---

## 💭 市场情绪分析报告
{sentiment_report}

---

## ⏱️ 性能统计

- **阶段1 (并行分析):** {exec_times.get('stage1_parallel_analysis', 0):.2f}秒  
  - 量化研究员 + 基本面研究员 + 情绪分析师
- **阶段2 (策略生成):** {exec_times.get('stage2_strategy_generation', 0):.2f}秒
- **阶段3 (风险审核):** {exec_times.get('stage3_risk_control', 0):.2f}秒
- **总耗时:** {exec_times.get('total_time', 0):.2f}秒
- **优化效果:** {exec_times.get('speedup_estimate', 'N/A')}

*本报告由AI多Agent系统自动生成（并发优化版），仅供参考，不构成投资建议*
"""
    
    # Handle old workflow (v1.0) - backward compatibility
    else:
        fund_manager_report = ai_results.get('fund_manager', {}).get('report', '基金经理报告不可用。')
        data_analyst_report = ai_results.get('data_analyst', {}).get('report', '数据分析报告不可用。')
        market_analyst_report = ai_results.get('market_analyst', {}).get('report', '市场分析报告不可用。')
        
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

*本报告由AI多Agent系统自动生成，仅供参考，不构成投资建议*
"""
