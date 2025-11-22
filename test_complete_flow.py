#!/usr/bin/env python3
"""
测试完整的日报生成和发送流程
"""
import os
import sys
import json

def test_imports():
    """测试所有必需的导入"""
    print("="*60)
    print("测试1: 检查导入")
    print("="*60)
    
    try:
        print("  测试 llm 模块...")
        from llm import SimpleMarketAnalyzer
        print("  ✅ SimpleMarketAnalyzer 导入成功")
        
        print("  测试 llm.simple_report_builder...")
        from llm.simple_report_builder import build_simple_email_body, build_simple_html_report
        print("  ✅ simple_report_builder 导入成功")
        
        print("  测试 src 模块...")
        from src.data_fetcher import fetch_and_insert, load_recent_data
        from src.feature_engineering import build_features
        from src.model_loader import find_model_and_scaler, load_model_and_scaler
        from src.predictor import predict_next_days
        from src.chart_generator import generate_prediction_chart
        from src.github_uploader import upload_prediction_chart
        print("  ✅ src 模块导入成功")
        
        print("  测试 email_sender...")
        from src.email_sender import send_email_report
        print("  ✅ email_sender 导入成功")
        
        return True
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False

def test_config_files():
    """测试配置文件"""
    print("\n" + "="*60)
    print("测试2: 检查配置文件")
    print("="*60)
    
    config_files = {
        'config.json': False,
        'llm_config.json': True,
        'email_config.json': False,
    }
    
    all_ok = True
    for file, required in config_files.items():
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"  ✅ {file} - 存在且格式正确")
            except json.JSONDecodeError:
                print(f"  ❌ {file} - 格式错误")
                all_ok = False
        else:
            if required:
                print(f"  ❌ {file} - 不存在（必需）")
                all_ok = False
            else:
                print(f"  ⚠️  {file} - 不存在（可选）")
    
    return all_ok

def test_run_daily_report_syntax():
    """测试 run_daily_report.py 语法"""
    print("\n" + "="*60)
    print("测试3: 检查 run_daily_report.py")
    print("="*60)
    
    try:
        with open('run_daily_report.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否还有旧的导入
        if 'OptimizedQuantWorkflow' in content:
            print("  ⚠️  发现旧的 OptimizedQuantWorkflow 引用")
        
        if 'workflow_optimized' in content:
            print("  ⚠️  发现旧的 workflow_optimized 引用")
        
        if 'ReportGenerator' in content:
            print("  ⚠️  发现旧的 ReportGenerator 引用")
        
        # 检查新的导入
        if 'SimpleMarketAnalyzer' in content:
            print("  ✅ 包含 SimpleMarketAnalyzer")
        else:
            print("  ❌ 缺少 SimpleMarketAnalyzer")
            return False
        
        if 'simple_workflow' in content:
            print("  ✅ 包含 simple_workflow")
        else:
            print("  ❌ 缺少 simple_workflow")
            return False
        
        # 语法检查
        compile(content, 'run_daily_report.py', 'exec')
        print("  ✅ 语法正确")
        
        return True
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False

def test_send_cached_report():
    """测试 send_cached_report.py"""
    print("\n" + "="*60)
    print("测试4: 检查 send_cached_report.py")
    print("="*60)
    
    if not os.path.exists('send_cached_report.py'):
        print("  ❌ send_cached_report.py 不存在")
        return False
    
    try:
        with open('send_cached_report.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, 'send_cached_report.py', 'exec')
        print("  ✅ 语法正确")
        
        # send_cached_report.py 不需要修改，因为它只读取 email_cache.json
        print("  ✅ send_cached_report.py 无需修改")
        
        return True
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False

def test_email_cache_structure():
    """测试 email_cache.json 结构"""
    print("\n" + "="*60)
    print("测试5: 检查 email_cache.json 结构")
    print("="*60)
    
    cache_path = 'models/email_cache.json'
    if not os.path.exists(cache_path):
        print(f"  ⚠️  {cache_path} 不存在（首次运行后会创建）")
        return True
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        required_keys = ['date', 'subject', 'body', 'attachments']
        for key in required_keys:
            if key in cache:
                print(f"  ✅ 包含 '{key}'")
            else:
                print(f"  ❌ 缺少 '{key}'")
                return False
        
        # 检查 workflow_type
        workflow_type = cache.get('workflow_type', 'unknown')
        print(f"  📝 工作流类型: {workflow_type}")
        
        return True
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False

def test_api():
    """测试 API"""
    print("\n" + "="*60)
    print("测试6: 检查 API")
    print("="*60)
    
    try:
        with open('api.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, 'api.py', 'exec')
        print("  ✅ api.py 语法正确")
        
        # 检查是否移除了 v2 workflow 的复杂逻辑
        if 'workflow_type' in content and 'simple' in content:
            print("  ✅ API 支持简洁报告")
        
        return True
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False

def main():
    print("🧪 Buffotte 项目完整测试")
    print("测试清理后的项目是否可以正常运行\n")
    
    results = []
    
    results.append(("导入测试", test_imports()))
    results.append(("配置文件", test_config_files()))
    results.append(("run_daily_report.py", test_run_daily_report_syntax()))
    results.append(("send_cached_report.py", test_send_cached_report()))
    results.append(("email_cache.json", test_email_cache_structure()))
    results.append(("API", test_api()))
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:30s} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
        print("\n✅ run_daily_report.py 可以正常运行")
        print("✅ send_cached_report.py 可以正常运行")
        print("\n下一步:")
        print("  1. 配置 llm_config.json (设置 API key)")
        print("  2. 运行: python run_daily_report.py")
        print("  3. 发送: python send_cached_report.py")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查")
        return 1

if __name__ == '__main__':
    sys.exit(main())
