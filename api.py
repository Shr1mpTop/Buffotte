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
    获取报告的摘要信息（简洁版）
    
    Returns:
        包含市场状态和操作建议的字典
    """
    cache_path = os.path.join("models", "email_cache.json")
    
    if not os.path.exists(cache_path):
        raise HTTPException(status_code=404, detail="Report not found. Please run daily report generation first.")
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        
        ai_summary = report_data.get("ai_results_summary", {})
        metrics = ai_summary.get("metrics", {})
        insights = ai_summary.get("insights", {})
        
        return {
            "status": "success",
            "generated_at": report_data.get("generated_at"),
            "date": report_data.get("date"),
            "summary": insights.get("summary", ""),
            "action": insights.get("action", "观望"),
            "confidence": insights.get("confidence", 50),
            "reason": insights.get("reason", ""),
            "price": metrics.get("price", {}),
            "volume": metrics.get("volume", {}),
            "sentiment": metrics.get("sentiment", {}),
            "technical": metrics.get("technical", {})
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid report format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading report: {str(e)}")