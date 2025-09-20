"""
Buffotte 主程序入口
用于启动单个物品更新或批量爬虫
"""
import argparse
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='Buffotte 爬虫工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 单个物品更新命令
    single_parser = subparsers.add_parser('single', help='更新单个物品')
    single_parser.add_argument('item_name', help='物品名称')
    single_parser.add_argument('--config', type=str, default='./config.json', help='配置文件路径')
    
    # 批量爬取命令
    batch_parser = subparsers.add_parser('batch', help='批量爬取物品')
    batch_parser.add_argument('--max-pages', type=int, help='总共要爬取的页面数')
    batch_parser.add_argument('--threads', type=int, help='爬虫线程数')
    batch_parser.add_argument('--config', type=str, default='./config.json', help='配置文件路径')
    
    args = parser.parse_args()
    
    if args.command == 'single':
        # 导入并调用单个物品更新功能
        from crawler.single_item_updater import update_single_item
        
        # 检查是否是物品ID（纯数字）
        item_identifier = args.item_name
        is_id = item_identifier.isdigit()
        
        if is_id:
            # 如果是ID，转换为整数
            result = await update_single_item(int(item_identifier), None, args.config)
        else:
            # 如果是名称，按名称处理
            result = await update_single_item(None, item_identifier, args.config)
            
        if result:
            print(f"成功更新物品: {item_identifier}")
        else:
            print(f"更新物品失败: {item_identifier}")
    
    elif args.command == 'batch':
        # 导入并调用批量爬虫功能
        from crawler.batch_crawler import main as batch_main
        # 将参数传递给批量爬虫
        sys.argv = ['batch_crawler.py']
        if args.max_pages:
            sys.argv.extend(['--max-pages', str(args.max_pages)])
        if args.threads:
            sys.argv.extend(['--threads', str(args.threads)])
        if args.config:
            sys.argv.extend(['--config', args.config])
        
        await batch_main()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())