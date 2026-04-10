"""
skin_investigator.py — Phase 4: Investigator Agent

从 skin_search_tasks 中获取待处理任务，通过 buff-tracker 服务获取
K 线数据，并将结果持久化到 skin_details 表。
"""

import time
import sys
import os
import logging
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
load_dotenv()

from db.skin_processor import (
    SkinEntityProcessor,
    SkinSearchTaskProcessor,
    SkinDetailProcessor,
)
from db.item_kline_processor import ItemKlineProcessor

AGENT_ID = "skin_investigator_v1"
CRAWL_DELAY_SECONDS = 2   # buff-tracker 间隔不需要太长
DEFAULT_BATCH_SIZE = 10   # 每次批量处理的任务数
DEFAULT_PLATFORM = "BUFF"

# buff-tracker 服务地址
BUFFTRACKER_URL = os.getenv("BUFFTRACKER_URL", "http://host.docker.internal:8001")

# 用于从 cs2_items 查找完整的 market_hash_name（含品质后缀）
_kline_processor = ItemKlineProcessor()


def _normalize_hash_name(name: str) -> str:
    """修正常见的 market_hash_name 格式问题。"""
    if not name:
        return name
    # 去除 LLM 解析残留的前缀杂文
    for prefix in ("and 30 days show ", "N skins like "):
        if name.startswith(prefix):
            name = name[len(prefix):]
    # 补全缺失的管道符：'M4A4 Neon Rider' → 'M4A4 | Neon Rider'
    weapon_prefixes = [
        "AK-47", "M4A4", "M4A1-S", "AWP", "USP-S", "Glock-18", "Desert Eagle",
        "P250", "CZ75-Auto", "Five-SeveN", "Tec-9", "MP9", "MP7", "MP5-SD",
        "UMP-45", "P90", "PP-Bizon", "MAC-10", "MAG-7", "Nova", "XM1014",
        "Sawed-Off", "Negev", "M249", "FAMAS", "Galil AR", "SG 553", "AUG",
        "SSG 08", "SCAR-20", "G3SG1", "P2000", "R8 Revolver", "Dual Berettas",
    ]
    for wp in weapon_prefixes:
        if name.startswith(wp + " ") and " | " not in name:
            name = wp + " | " + name[len(wp) + 1:]
            break
    return name.strip()


def _lookup_full_hash_name(market_hash_name: str) -> str:
    """
    从 cs2_items 表查找完整的 market_hash_name（含品质后缀如 Field-Tested）。
    buff-tracker 需要完整名称来获取 kline 数据。
    三级匹配：精确 → 前缀 LIKE → 包含 LIKE（处理 ★ 前缀的刀具/手套）。
    """
    conn = None
    try:
        conn = _kline_processor.get_db_connection()
        with conn.cursor() as cursor:
            # 精确匹配
            cursor.execute(
                "SELECT market_hash_name FROM cs2_items WHERE market_hash_name = %s LIMIT 1",
                (market_hash_name,)
            )
            row = cursor.fetchone()
            if row:
                return str(row[0])

            # 前缀匹配：hash + 品质后缀 (Field-Tested) 等
            cursor.execute(
                "SELECT market_hash_name FROM cs2_items WHERE market_hash_name LIKE %s LIMIT 1",
                (f"{market_hash_name}%",)
            )
            row = cursor.fetchone()
            if row:
                return str(row[0])

            # 包含匹配：处理 ★ 前缀的刀具/手套/Souvenir 等
            cursor.execute(
                "SELECT market_hash_name FROM cs2_items WHERE market_hash_name LIKE %s LIMIT 1",
                (f"%{market_hash_name}%",)
            )
            row = cursor.fetchone()
            if row:
                return str(row[0])
    except Exception as e:
        logger.warning(f"查找完整名称失败: {e}")
    finally:
        if conn and conn.open:
            conn.close()

    return ""


def _search_hash_name_via_bufftracker(chinese_name: str) -> str:
    """
    通过 buff-tracker 的 /api/search 接口，用中文名搜索获取 market_hash_name。
    作为 cs2_items 本地查找失败时的保底机制。
    返回第一个匹配结果的 market_hash_name，失败返回空字符串。
    """
    url = f"{BUFFTRACKER_URL}/api/search"
    try:
        resp = httpx.get(url, params={"name": chinese_name}, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") and data.get("data"):
            first = data["data"][0]
            hash_name = first.get("market_hash_name", "")
            logger.info(f"    搜索保底: '{chinese_name}' → '{hash_name}'")
            return hash_name
        logger.warning(f"    搜索保底无结果: '{chinese_name}'")
        return ""
    except Exception as e:
        logger.error(f"    搜索保底请求失败: {e}")
        return ""


def _fetch_kline_from_bufftracker(
    market_hash_name: str,
    platform: str = "BUFF",
    type_day: str = "2",
) -> dict | None:
    """
    通过 buff-tracker 服务获取 K 线数据。
    buff-tracker 内部使用 Playwright+Chrome 绕过 steamdt WAF。
    返回格式: {success: True, data: [[ts, price, sell, buy_price, buy_count, turnover, volume, total], ...]}
    """
    url = f"{BUFFTRACKER_URL}/api/item/kline-data/{quote(market_hash_name)}"
    params = {"platform": platform, "type_day": type_day, "date_type": "3"}
    try:
        resp = httpx.get(url, params=params, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") and data.get("data"):
            return data
        logger.warning(f"buff-tracker 返回无数据: {data.get('errorMsg', data.get('detail', ''))}")
        return None
    except Exception as e:
        logger.error(f"buff-tracker 请求失败: {e}")
        return None


def _extract_price_from_kline(kline_data: dict) -> tuple[float | None, float | None, float | None, int | None]:
    """
    从 buff-tracker kline 响应里提取最新价格、24h变化率、7d变化率、成交量。
    buff-tracker data 格式: [[timestamp, price, sell_count, buy_price, buy_count, turnover, volume, total_count], ...]
    返回 (current_price, price_change_24h, price_change_7d, volume)
    """
    try:
        rows = kline_data.get("data", [])
        if not rows or not isinstance(rows, list):
            return None, None, None, None

        latest = rows[-1]
        if not isinstance(latest, (list, tuple)) or len(latest) < 2:
            return None, None, None, None

        current_price = float(latest[1]) if latest[1] is not None else None
        volume = int(latest[6]) if len(latest) > 6 and latest[6] is not None else None

        if current_price is None:
            return None, None, None, None

        # 24h 变化率
        price_change_24h = None
        if len(rows) >= 2:
            prev = rows[-2]
            prev_price = float(prev[1]) if prev[1] is not None else 0
            if prev_price > 0:
                price_change_24h = (current_price - prev_price) / prev_price

        # 7d 变化率
        price_change_7d = None
        if len(rows) >= 8:
            week_ago = rows[-8]
            week_price = float(week_ago[1]) if week_ago[1] is not None else 0
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

                        # 修正 hash name 格式问题
                        if market_hash_name:
                            market_hash_name = _normalize_hash_name(market_hash_name)

                        if not market_hash_name:
                            # 无 market_hash_name 则无法爬取 steamdt
                            logger.warning(f"  任务 #{task_id} [{skin_name}]: 缺少 market_hash_name，跳过")
                            task_proc.update_task_status(task_id, 'failed', error_message="no market_hash_name")
                            stats["skipped"] += 1
                            continue

                        logger.info(f"  [{i+1}/{len(tasks)}] 调查: {skin_name} ({market_hash_name})")

                        # 查找带品质后缀的完整名称（buff-tracker 需要完整名称）
                        full_name = _lookup_full_hash_name(market_hash_name)
                        if full_name:
                            logger.info(f"    完整名称: {full_name}")
                        else:
                            # 找不到完整名称，尝试用原始名称
                            full_name = market_hash_name
                            logger.warning(f"    未匹配到完整名称，使用原始: {full_name}")

                        # 标记任务为运行中
                        task_proc.update_task_status(task_id, 'running', assigned_agent=AGENT_ID)

                        # 通过 buff-tracker 获取 K 线数据
                        kline_result = None
                        try:
                            kline_result = _fetch_kline_from_bufftracker(
                                market_hash_name=full_name,
                                platform=self.platform,
                                type_day="2",
                            )
                        except Exception as e:
                            logger.error(f"    获取失败: {e}")

                        # 保底机制：kline 获取失败时，用中文名通过 search API 查找 hash name 后重试
                        if not kline_result and skin_name:
                            logger.info(f"    触发搜索保底，使用中文名: {skin_name}")
                            fallback_name = _search_hash_name_via_bufftracker(skin_name)
                            if fallback_name and fallback_name != full_name:
                                time.sleep(CRAWL_DELAY_SECONDS)
                                try:
                                    kline_result = _fetch_kline_from_bufftracker(
                                        market_hash_name=fallback_name,
                                        platform=self.platform,
                                        type_day="2",
                                    )
                                    if kline_result:
                                        # 保底成功，回写正确的 market_hash_name 到实体
                                        entity_proc.update_market_hash_name(entity_id, fallback_name)
                                        logger.info(f"    保底成功，已更新 hash_name: {fallback_name}")
                                except Exception as e:
                                    logger.error(f"    保底获取失败: {e}")

                        if not kline_result:
                            logger.warning(f"    buff-tracker 返回为空")
                            task_proc.update_task_status(task_id, 'failed', error_message="empty kline from bufftracker")
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
