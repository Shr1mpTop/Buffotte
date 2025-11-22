from fastapi import FastAPI, HTTPException
import json
import os
from typing import Dict, Any

app = FastAPI(title="Buffotte Report API", description="API for accessing daily market analysis reports")

@app.get("/")
def read_root():
    return {"message": "Welcome to Buffotte Report API"}

@app.get("/report")
def get_daily_report() -> Dict[str, Any]:
    """
    获取最新的每日报告
    
    Returns:
        包含报告内容的字典，包括AI分析、市场预测等
    """
    cache_path = os.path.join("models", "email_cache.json")
    
    if not os.path.exists(cache_path):
        raise HTTPException(status_code=404, detail="Report not found. Please run daily report generation first.")
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        
        return {
            "status": "success",
            "data": report_data
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid report format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading report: {str(e)}")

@app.get("/report/markdown")
def get_markdown_report() -> Dict[str, str]:
    """
    获取报告的Markdown格式内容
    
    Returns:
        包含Markdown报告的字典
    """
    cache_path = os.path.join("models", "email_cache.json")
    
    if not os.path.exists(cache_path):
        raise HTTPException(status_code=404, detail="Report not found. Please run daily report generation first.")
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        
        markdown_content = report_data.get("markdown_report", "")
        
        return {
            "status": "success",
            "markdown": markdown_content
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid report format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading report: {str(e)}")

@app.get("/report/summary")
def get_report_summary() -> Dict[str, Any]:
    """
    获取报告的摘要信息
    
    Returns:
        包含执行摘要和关键信息的字典
    """
    cache_path = os.path.join("models", "email_cache.json")
    
    if not os.path.exists(cache_path):
        raise HTTPException(status_code=404, detail="Report not found. Please run daily report generation first.")
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        
        ai_summary = report_data.get("ai_results_summary", {})
        executive_summary = ai_summary.get("executive_summary", {})
        
        return {
            "status": "success",
            "generated_at": report_data.get("generated_at"),
            "date": report_data.get("date"),
            "executive_summary": executive_summary,
            "ai_analysis": {
                "quant_researcher": ai_summary.get("quant_researcher", {}).get("key_findings", []),
                "fundamental_analyst": ai_summary.get("fundamental_analyst", {}).get("key_findings", []),
                "sentiment_analyst": ai_summary.get("sentiment_analyst", {}).get("key_findings", []),
                "strategy_manager": ai_summary.get("strategy_manager", {}).get("key_findings", []),
                "risk_control": ai_summary.get("risk_control", {}).get("key_findings", [])
            }
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid report format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading report: {str(e)}")