"""
orchestrator.py — Phase 5: Pipeline Orchestrator

组织整个流水线：Scout Agent → Parser Agent → Investigator Agent
支持单次运行和定时运行模式。
"""

import sys
import os
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from llm.agents.scout_agent import ScoutAgent, DEFAULT_SEARCH_TOPICS
from llm.agents.skin_parser import SkinParserAgent
from llm.agents.skin_investigator import SkinInvestigatorAgent


def run_pipeline(
    topics: list = None,
    scout_max_tool_calls: int = 3,
    scout_limit: int = 10,
    parser_batch_size: int = None,
    investigator_batch_size: int = 10,
    skip_scout: bool = False,
    scout_result_file: str = None,
) -> dict:
    """
    运行完整的 CS2 饰品智能分析流水线。

    Args:
        topics: Scout 搜索话题列表，None 使用默认。
        scout_max_tool_calls: Scout 最大工具调用轮次。
        scout_limit: Scout 单轮搜索返回最大结果数。
        parser_batch_size: Parser 一次处理的 references 上限（None=不限）。
        investigator_batch_size: Investigator 一次处理的任务数。
        skip_scout: 跳过 Scout 阶段（用于调试，配合 scout_result_file）。
        scout_result_file: 指定 Scout 响应文件（skip_scout=True 时使用）。

    Returns:
        包含各阶段统计的字典。
    """
    start_time = datetime.now()
    pipeline_stats = {
        "started_at": start_time.isoformat(),
        "scout": {},
        "parser": {},
        "investigator": {},
    }

    logger.info(f"[Orchestrator] 启动流水线 @ {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # ─── Phase 1: Scout Agent ─────────────────────────────────────
    scout_results = []
    if skip_scout and scout_result_file:
        # 直接加载已有响应文件
        import json
        logger.info(f"[Phase 1] Scout: 加载响应文件 {os.path.basename(scout_result_file)}")
        try:
            with open(scout_result_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            # 还原为 search() 方法返回的格式（兼容 Parser 的 parse() 方法）
            references = ScoutAgent._extract_references(raw_data)
            summary_text = ScoutAgent._extract_summary_text(raw_data)
            single_result = {
                "response_data": raw_data,
                "references": references,
                "summary_text": summary_text,
                "reference_count": len(references),
                "health": {"is_healthy": True},
            }
            scout_results = [single_result]
            pipeline_stats["scout"] = {"skipped": True, "loaded_file": scout_result_file,
                                       "references": len(references)}
        except Exception as e:
            logger.error(f"  加载文件失败: {e}")
            return pipeline_stats
    else:
        logger.info(f"[Phase 1] Scout: 开始搜索 {len(topics or DEFAULT_SEARCH_TOPICS)} 个话题")
        try:
            scout = ScoutAgent()
            for topic in (topics or DEFAULT_SEARCH_TOPICS):
                logger.info(f"  搜索话题: {topic['name']}")
                result = scout.search(
                    topic,
                    max_tool_calls=scout_max_tool_calls,
                    limit=scout_limit,
                )
                if result.get("health", {}).get("is_healthy"):
                    # 持久化到 DB
                    scout.process_to_db(result)
                    scout_results.append(result)
                    logger.info(f"  找到 {result.get('reference_count', 0)} 条引用")
                else:
                    logger.warning(f"  搜索结果不健康，跳过")
                    scout_results.append(result)

                # 话题间稍作间隔
                time.sleep(2)

            pipeline_stats["scout"] = {
                "topics_searched": len(scout_results),
                "total_references": sum(r.get("reference_count", 0) for r in scout_results),
            }
        except Exception as e:
            logger.error(f"  Scout 阶段失败: {e}")
            pipeline_stats["scout"]["error"] = str(e)

    # ─── Phase 2: Parser Agent ────────────────────────────────────
    logger.info(f"[Phase 2] Parser: 从 {len(scout_results)} 条搜索结果中提取饰品实体")
    total_entities = 0
    total_tasks_created = 0
    try:
        parser = SkinParserAgent()
        for result in scout_results:
            if not result:
                continue
            parse_result = parser.parse(result)
            entity_count = len(parse_result.get("entities", []))
            tasks_count = parse_result.get("tasks_created", 0)
            total_entities += entity_count
            total_tasks_created += tasks_count
            logger.info(f"  提取 {entity_count} 个实体，创建 {tasks_count} 个任务")

        pipeline_stats["parser"] = {
            "total_entities": total_entities,
            "total_tasks_created": total_tasks_created,
        }
    except Exception as e:
        logger.error(f"  Parser 阶段失败: {e}")
        pipeline_stats["parser"]["error"] = str(e)

    # ─── Phase 3: Investigator Agent ──────────────────────────────
    logger.info(f"[Phase 3] Investigator: 处理最多 {investigator_batch_size} 个调查任务")
    try:
        investigator = SkinInvestigatorAgent(batch_size=investigator_batch_size)
        inv_stats = investigator.run_pending_tasks()
        pipeline_stats["investigator"] = inv_stats
    except Exception as e:
        logger.error(f"  Investigator 阶段失败: {e}")
        pipeline_stats["investigator"]["error"] = str(e)

    # ─── 完成 ──────────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    pipeline_stats["elapsed_seconds"] = elapsed
    pipeline_stats["finished_at"] = datetime.now().isoformat()

    logger.info(f"[Orchestrator] 流水线完成，耗时 {elapsed:.1f}s | Scout: {pipeline_stats['scout']} | Parser: {pipeline_stats['parser']} | Investigator: {pipeline_stats['investigator']}")

    return pipeline_stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CS2 饰品智能分析流水线")
    parser.add_argument("--skip-scout", action="store_true", help="跳过 Scout 阶段")
    parser.add_argument("--scout-file", type=str, default=None,
                        help="指定 Scout 响应 JSON 文件路径（配合 --skip-scout 使用）")
    parser.add_argument("--investigator-batch", type=int, default=10,
                        help="Investigator 每次处理任务数（默认 10）")
    args = parser.parse_args()

    # 自动查找最新 scout 文件
    if args.skip_scout and not args.scout_file:
        responses_dir = os.path.join(os.path.dirname(__file__), 'responses')
        if os.path.isdir(responses_dir):
            files = sorted(
                [f for f in os.listdir(responses_dir) if f.startswith('scout_') and f.endswith('.json')],
                reverse=True
            )
            if files:
                args.scout_file = os.path.join(responses_dir, files[0])
                logger.info(f"[Orchestrator] 自动选择最新 Scout 文件: {files[0]}")

    run_pipeline(
        skip_scout=args.skip_scout,
        scout_result_file=args.scout_file,
        investigator_batch_size=args.investigator_batch,
    )
