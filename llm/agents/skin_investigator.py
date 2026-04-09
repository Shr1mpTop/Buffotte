"""
skin_investigator.py — Phase 4: Investigator Agent

从 skin_search_tasks 中获取待处理任务，使用 crawler/item_price.py 爬取
steamdt.com 的 K 线数据，并将结果持久化到 skin_details 表。
"""

import time
import sys
import os
import logging

logger = logging.getLogger(__name__)

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from crawler.item_price import DailyKlineCrawler
from db.skin_processor import (
    SkinEntityProcessor,
    SkinSearchTaskProcessor,
    SkinDetailProcessor,
)
from db.item_kline_processor import ItemKlineProcessor

AGENT_ID = "skin_investigator_v1"
CRAWL_DELAY_SECONDS = 5   # 两次爬取之间的等待时间（避免触发反爬）
DEFAULT_BATCH_SIZE = 10   # 每次批量处理的任务数
DEFAULT_PLATFORM = "BUFF"

# 用于从 cs2_items 查找 item_id
_kline_processor = ItemKlineProcessor()


def _lookup_item_id(market_hash_name: str) -> str:
    """
    从 cs2_items 表查找 item_id（c5_id）。
    先精确匹配，如果没匹配到，用 LIKE 模糊匹配（市场名含品质后缀如 (Field-Tested)）。
    """
    item_id = _kline_processor.get_item_id_from_db(market_hash_name)
    if item_id:
        return item_id

    # 模糊匹配：market_hash_name 可能缺少品质后缀
    try:
        conn = _kline_processor.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT c5_id FROM cs2_items WHERE market_hash_name LIKE %s LIMIT 1",
                (f"{market_hash_name}%",)
            )
            row = cursor.fetchone()
            if row:
                return str(row[0])
    except Exception as e:
        logger.warning(f"模糊查找 item_id 失败: {e}")
    finally:
        if conn:
            conn.close()

    return ""


def _extract_price_from_kline(kline_data: dict) -> tuple[float | None, float | None, float | None, int | None]:
    """
    从 kline 响应数据里提取最新价格、24h变化率、7d变化率、成交量。
    返回 (current_price, price_change_24h, price_change_7d, volume)
    """
    try:
        data = kline_data.get("data", {})
        if not data:
            return None, None, None, None

        # steamdt kline 数据结构：data.klines 是列表，每项 [时间戳, 开, 高, 低, 收, 量]
        klines = data.get("klines") or data.get("list") or []
        if not klines:
            # 尝试备用字段
            price = data.get("price") or data.get("currentPrice")
            return (float(price) if price else None), None, None, None

        # 取最新一条
        latest = klines[-1]
        if isinstance(latest, (list, tuple)) and len(latest) >= 5:
            current_price = float(latest[4])   # 收盘价
            volume = int(latest[5]) if len(latest) > 5 else None
        elif isinstance(latest, dict):
            current_price = float(latest.get('close') or latest.get('c') or 0)
            volume = latest.get('volume') or latest.get('v')
        else:
            return None, None, None, None

        # 计算 24h 变化率（用最近两条）
        price_change_24h = None
        if len(klines) >= 2:
            prev = klines[-2]
            prev_price = float(prev[4]) if isinstance(prev, (list, tuple)) else float(prev.get('close') or prev.get('c') or 0)
            if prev_price > 0:
                price_change_24h = (current_price - prev_price) / prev_price

        # 计算 7d 变化率（用最近8条的第一条）
        price_change_7d = None
        if len(klines) >= 8:
            week_ago = klines[-8]
            week_price = float(week_ago[4]) if isinstance(week_ago, (list, tuple)) else float(week_ago.get('close') or week_ago.get('c') or 0)
            if week_price > 0:
                price_change_7d = (current_price - week_price) / week_price

        return current_price, price_change_24h, price_change_7d, volume

    except Exception as e:
        logger.error(f"  [Investigator] 解析 kline 数据失败: {e}")
        return None, None, None, None


class SkinInvestigatorAgent:
    """
    调查员 Agent：负责爬取各饰品的价格 K 线数据，并写入 DB。
    """

    def __init__(self, batch_size: int = DEFAULT_BATCH_SIZE, platform: str = DEFAULT_PLATFORM):
        self.batch_size = batch_size
        self.platform = platform
        self.crawler = DailyKlineCrawler()

    def run_pending_tasks(self) -> dict:
        """
        主入口：从 DB 获取 pending 任务，逐一爬取，更新 DB。
        返回运行统计。
        """
        stats = {"total": 0, "succeeded": 0, "failed": 0, "skipped": 0}

        with SkinSearchTaskProcessor() as task_proc:
            if not task_proc.conn:
                logger.error("[Investigator] DB 连接失败")
                return stats

            tasks = task_proc.get_pending_tasks(limit=self.batch_size)
            stats["total"] = len(tasks)

            if not tasks:
                logger.info("[Investigator] 没有待处理的任务")
                return stats

            logger.info(f"[Investigator] 获取到 {len(tasks)} 个待处理任务")

            with SkinEntityProcessor() as entity_proc:
                with SkinDetailProcessor() as detail_proc:
                    detail_proc.create_table_if_not_exists()

                    for i, task in enumerate(tasks):
                        task_id = task['id']
                        entity_id = task['skin_entity_id']

                        # 获取饰品实体信息
                        entity = entity_proc.get_skin_entity_by_id(entity_id)
                        if not entity:
                            logger.warning(f"  任务 #{task_id}: 找不到实体 ID={entity_id}，跳过")
                            task_proc.update_task_status(task_id, 'failed', error_message="entity not found")
                            stats["skipped"] += 1
                            continue

                        skin_name = entity.get('skin_name', '未知')
                        market_hash_name = entity.get('market_hash_name')

                        if not market_hash_name:
                            # 无 market_hash_name 则无法爬取 steamdt
                            logger.warning(f"  任务 #{task_id} [{skin_name}]: 缺少 market_hash_name，跳过")
                            task_proc.update_task_status(task_id, 'failed', error_message="no market_hash_name")
                            stats["skipped"] += 1
                            continue

                        logger.info(f"  [{i+1}/{len(tasks)}] 调查: {skin_name} ({market_hash_name})")

                        # 从 cs2_items 查找 steamdt item_id
                        item_id = _lookup_item_id(market_hash_name)
                        if not item_id:
                            logger.warning(f"    未找到 item_id，将尝试使用 hashname 爬取")

                        # 标记任务为运行中
                        task_proc.update_task_status(task_id, 'running', assigned_agent=AGENT_ID)

                        # 爬取 K 线数据（steamdt）
                        kline_result = None
                        try:
                            kline_result = self.crawler.fetch_item_details(
                                item_id=item_id,
                                platform=self.platform,
                                type_day="2",         # 2=日K
                                hashname=market_hash_name,
                            )
                        except Exception as e:
                            logger.error(f"    爬取失败: {e}")
                            task_proc.update_task_status(task_id, 'failed', error_message=str(e))
                            stats["failed"] += 1
                            if i < len(tasks) - 1:
                                time.sleep(CRAWL_DELAY_SECONDS)
                            continue

                        if not kline_result:
                            logger.warning(f"    爬取结果为空")
                            task_proc.update_task_status(task_id, 'failed', error_message="empty kline result")
                            stats["failed"] += 1
                            if i < len(tasks) - 1:
                                time.sleep(CRAWL_DELAY_SECONDS)
                            continue

                        # 解析价格数据
                        current_price, change_24h, change_7d, volume = _extract_price_from_kline(kline_result)

                        # 写入 skin_details
                        detail_id = detail_proc.upsert_skin_detail(
                            skin_entity_id=entity_id,
                            platform=self.platform,
                            current_price=current_price,
                            price_change_24h=change_24h,
                            price_change_7d=change_7d,
                            volume=volume,
                            kline_data_json=kline_result,
                        )

                        price_str = f"¥{current_price:.2f}" if current_price else "N/A"
                        change_str = f"{change_24h*100:+.2f}%" if change_24h is not None else "N/A"
                        logger.info(f"    价格: {price_str}  24h: {change_str}  detail_id={detail_id}")

                        # 更新任务状态为完成
                        task_proc.update_task_status(
                            task_id, 'done',
                            result_json={"current_price": current_price, "change_24h": change_24h,
                                         "change_7d": change_7d, "volume": volume, "detail_id": detail_id}
                        )
                        stats["succeeded"] += 1

                        # 爬取间隔
                        if i < len(tasks) - 1:
                            time.sleep(CRAWL_DELAY_SECONDS)

        logger.info(f"[Investigator] 完成: 共 {stats['total']} 任务 | "
              f"成功 {stats['succeeded']} | 失败 {stats['failed']} | 跳过 {stats['skipped']}")
        return stats


if __name__ == "__main__":
    agent = SkinInvestigatorAgent(batch_size=5)
    agent.run_pending_tasks()
