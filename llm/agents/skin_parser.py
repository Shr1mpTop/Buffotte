"""
Skin Parser Agent（饰品解析代理）

职责：
1. 接收 Scout Agent 的搜索响应数据
2. 从 url_citation annotations 中提取具体的饰品名称实体
3. 调用 LLM 分析 annotation summaries，识别饰品实体、武器类型、价格事件
4. 将饰品实体写入 skin_entities 表（upsert）
5. 为每个需要深度调查的饰品创建 skin_search_tasks 任务
6. 返回提取到的饰品实体列表
"""

import os
import json
import re
import logging
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


# 武器类型关键词映射
WEAPON_TYPE_KEYWORDS = {
    "knife": ["刀", "弯刀", "蝴蝶刀", "爪子刀", "折叠刀", "暗影双匕", "骷髅刀", "海豹短刀",
              "系绳匕首", "猎杀者匕首", "穿肠刀", "弓形刀", "M9刺刀", "刺刀", "Karambit",
              "Butterfly", "Bayonet", "Bowie", "Falchion", "Flip", "Gut", "Huntsman",
              "Navaja", "Nomad", "Paracord", "Shadow Daggers", "Skeleton", "Stiletto",
              "Talon", "Ursus", "Classic Knife"],
    "glove": ["手套", "运动手套", "摩托手套", "驾驶手套", "手部布料", "九头蛇手套", "血猎手套",
              "Gloves", "Hand Wraps", "Hydra Gloves", "Bloodhound"],
    "rifle": ["AK", "M4A4", "M4A1", "FAMAS", "Galil", "SG553", "AUG", "SCAR", "AWP",
              "SSG08", "G3SG1", "步枪", "狙击"],
    "pistol": ["手枪", "Glock", "USP", "P2000", "CZ75", "Desert Eagle", "P250", "Five-Seven",
               "Tec-9", "R8", "沙漠之鹰", "格洛克"],
    "smg": ["冲锋枪", "MP9", "MAC-10", "PP-Bizon", "MP7", "UMP", "P90"],
    "shotgun": ["霰弹枪", "Nova", "MAG-7", "Sawed-Off", "XM1014"],
}

# 稀有度关键词
RARITY_KEYWORDS = {
    "消费级": ["消费级", "白色"],
    "工业级": ["工业级", "浅蓝"],
    "军规级": ["军规级", "蓝色"],
    "受限": ["受限", "紫色"],
    "保密": ["保密", "粉色", "红色"],
    "隐秘": ["隐秘", "红色", "稀有"],
    "非凡": ["非凡", "金色", "黄金", "金刀", "★"],
}

# 价格事件关键词（用于优先级判断）
PRICE_EVENT_KEYWORDS = [
    "暴涨", "暴跌", "涨价", "跌价", "价格波动", "价格飙升", "价格崩盘",
    "大涨", "大跌", "翻倍", "腰斩", "新高", "新低", "破纪录",
    "pump", "dump", "crash", "surge", "price spike", "ATH", "ATL",
]

# Parser Agent 的 LLM prompt
PARSER_SYSTEM_PROMPT = """你是一个专门分析CS2（Counter-Strike 2）饰品新闻的实体提取助手。
你的任务是从给定的新闻摘要文本中，识别并提取所有提到的具体CS2饰品名称。

提取规则：
1. 只提取具体的饰品名称，如"蝴蝶刀（虎牙）"、"Karambit | Fade"、"运动手套（迈阿密风云）"、"AK-47 | 红线"
2. 不要提取泛化描述，如"高价饰品"、"稀有皮肤"、"金色饰品"等
3. 如果能识别出英文名（Steam market_hash_name格式），请一并提供
4. 识别武器类型：knife(刀)、glove(手套)、rifle(步枪)、pistol(手枪)、smg(冲锋枪)等
5. 识别是否有价格事件（暴涨/暴跌/新发布）

输出格式必须是合法的 JSON 数组，每个元素包含：
{
  "cn_name": "中文名称",
  "en_name": "英文市场名称（如知道）或null",
  "weapon_type": "knife/glove/rifle/pistol/smg/shotgun/other",
  "has_price_event": true/false,
  "price_event_type": "surge/crash/new_release/none"
}

如果没有找到具体饰品名称，返回空数组 []。"""

PARSER_USER_TEMPLATE = """请从以下新闻摘要中提取CS2饰品名称：

---
{text}
---

只返回 JSON 数组，不要有其他内容。"""


class SkinParserAgent:
    """
    Parser Agent（解析代理）

    从 Scout Agent 的搜索结果中提取饰品实体，并分发调查任务。
    """

    def __init__(self, model: str = None):
        api_key = os.getenv("ARK_API_KEY")
        if not api_key:
            raise ValueError("未配置 ARK_API_KEY，请在 .env 中设置")

        # Parser 使用 flash 模型（快速、低成本），不需要联网
        if model is None:
            models_str = os.getenv("DOUBAO_MODEL", "").strip('[]')
            models = [m.strip() for m in models_str.split(',')]
            model = next((m for m in models if 'flash' in m),
                         models[0] if models else 'doubao-seed-1-6-flash-250828')

        self.model = model
        self.client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key,
        )

    def parse(self, scout_result: dict) -> dict:
        """
        解析 Scout Agent 的搜索结果，提取饰品实体。

        Args:
            scout_result: Scout Agent search() 方法返回的字典，
                          包含 response_data, references, summary_text

        Returns:
            包含 entities, tasks_created 的字典
        """
        references = scout_result.get('references', [])
        summary_text = scout_result.get('summary_text', '')

        if not references and not summary_text:
            logger.info("[Parser] 无可解析内容")
            return {"entities": [], "tasks_created": 0}

        # Step 1: 规则匹配（快速、无 API 调用）
        rule_entities = self._extract_by_rules(references, summary_text)
        logger.info(f"[Parser] 规则匹配: 发现 {len(rule_entities)} 个候选实体")

        # Step 2: LLM 语义提取（更精准）
        llm_entities = self._extract_by_llm(references, summary_text)
        logger.info(f"[Parser] LLM 提取: 发现 {len(llm_entities)} 个实体")

        # Step 3: 合并去重
        merged_entities = self._merge_entities(rule_entities, llm_entities)
        logger.info(f"[Parser] 合并后: {len(merged_entities)} 个唯一实体")

        # Step 4: 写入 DB 并创建任务
        tasks_created = self._save_entities_and_create_tasks(merged_entities, references)

        return {
            "entities": merged_entities,
            "tasks_created": tasks_created,
        }

    def _extract_by_rules(self, references: list, summary_text: str) -> list[dict]:
        """
        使用规则（关键词 + 正则）快速提取饰品实体。
        能处理常见格式：'XX | XX (XX)' 和中文名。
        """
        entities = []
        seen_names = set()

        all_text = summary_text or ""
        all_text += " ".join(
            (r.get('summary', '') or '') + " " + (r.get('title', '') or '')
            for r in references
        )

        # 匹配英文格式：武器 | 皮肤名称 (磨损)
        # 要求武器名以字母开头（过滤数字+文本的假阳性）
        en_pattern = re.compile(
            r'(?:★\s*)?(?:StatTrak™\s*)?'
            r'([A-Z][A-Za-z0-9\-\./]{0,8}(?:[ \-][A-Za-z0-9\-\.]+){0,3})\s*\|\s*'   # 武器名（最多4个单词，仅空格/连字符分隔）
            r'([A-Z][A-Za-z0-9 \-\']{1,35})'              # 皮肤名（首字母大写）
            r'(?:\s*\((Factory New|Minimal Wear|Field-Tested|Well-Worn|Battle-Scarred|'
            r'崭新出厂|略有磨损|久经沙场|破损不堪|战痕累累)\))?',
            re.UNICODE
        )

        for m in en_pattern.finditer(all_text):
            weapon = m.group(1).strip().rstrip('.')
            skin = m.group(2).strip()

            # 过滤明显不是饰品名的匹配
            if len(weapon) < 2 or len(weapon) > 25 or len(skin) < 2 or len(skin) > 35:
                continue
            # 过滤包含明显噪音词的匹配（URL、统计文本等）
            noise_words = ['prices', 'market', 'value', 'Counter-Strike', 'http', 'www',
                           'index', 'volume', 'trading', 'today', 'tracker', 'skins like']
            if any(nw.lower() in skin.lower() or nw.lower() in weapon.lower()
                   for nw in noise_words):
                continue

            en_name = f"{weapon} | {skin}"

            if en_name not in seen_names:
                seen_names.add(en_name)
                weapon_type = self._detect_weapon_type(weapon)
                has_price_event = self._detect_price_event(all_text, en_name)
                entities.append({
                    "cn_name": en_name,
                    "en_name": en_name,
                    "weapon_type": weapon_type,
                    "has_price_event": has_price_event,
                    "price_event_type": "surge" if has_price_event else "none",
                    "source": "rule",
                })

        # 匹配常见中文刀/手套名
        cn_knife_pattern = re.compile(
            r'(蝴蝶刀|爪子刀|折叠刀|弯刀|暗影双匕|骷髅刀|M9刺刀|猎杀者匕首|海豹短刀|穿肠刀|弓形刀)'
            r'[（(]([^）),，。\s]{1,15})[）)]'   # 要求有括号包裹皮肤名
        )
        for m in cn_knife_pattern.finditer(all_text):
            knife_type = m.group(1)
            skin = m.group(2)
            cn_name = f"{knife_type}（{skin}）"

            if cn_name not in seen_names:
                seen_names.add(cn_name)
                has_price_event = self._detect_price_event(all_text, cn_name)
                entities.append({
                    "cn_name": cn_name,
                    "en_name": None,
                    "weapon_type": "knife",
                    "has_price_event": has_price_event,
                    "price_event_type": "surge" if has_price_event else "none",
                    "source": "rule",
                })

        cn_glove_pattern = re.compile(
            r'(运动手套|摩托手套|驾驶手套|手部布料|九头蛇手套|血猎手套)'
            r'[（(]([^）),，。\s]{1,15})[）)]'   # 要求有括号包裹皮肤名
        )
        for m in cn_glove_pattern.finditer(all_text):
            glove_type = m.group(1)
            skin = m.group(2)
            cn_name = f"{glove_type}（{skin}）"

            if cn_name not in seen_names:
                seen_names.add(cn_name)
                has_price_event = self._detect_price_event(all_text, cn_name)
                entities.append({
                    "cn_name": cn_name,
                    "en_name": None,
                    "weapon_type": "glove",
                    "has_price_event": has_price_event,
                    "price_event_type": "surge" if has_price_event else "none",
                    "source": "rule",
                })

        return entities

    def _extract_by_llm(self, references: list, summary_text: str) -> list[dict]:
        """
        调用 LLM 从 annotation summaries 和摘要中提取饰品实体。
        只取前 5 条 annotation 避免超出 token 限制。
        """
        # 构建输入文本：摘要 + 前5条引用摘要
        text_parts = []
        if summary_text:
            text_parts.append(f"[整体摘要]\n{summary_text[:2000]}")

        for ref in references[:5]:
            title = ref.get('title', '')
            ref_summary = ref.get('summary', '')
            if title or ref_summary:
                text_parts.append(f"[新闻: {title}]\n{ref_summary[:500]}")

        if not text_parts:
            return []

        combined_text = "\n\n".join(text_parts)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PARSER_SYSTEM_PROMPT},
                    {"role": "user", "content": PARSER_USER_TEMPLATE.format(text=combined_text)},
                ],
                temperature=0.1,
                max_tokens=2000,
            )
            content = response.choices[0].message.content.strip()

            # 提取 JSON
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                entities_raw = json.loads(json_match.group())
                # 添加来源标记
                for entity in entities_raw:
                    entity['source'] = 'llm'
                return entities_raw
            else:
                logger.warning(f"[Parser] LLM 返回非 JSON 内容: {content[:100]}")
                return []
        except json.JSONDecodeError as e:
            logger.warning(f"[Parser] JSON 解析失败: {e}")
            return []
        except Exception as e:
            logger.error(f"[Parser] LLM 提取失败: {e}")
            return []

    @staticmethod
    def _merge_entities(rule_entities: list, llm_entities: list) -> list[dict]:
        """
        合并两个来源的实体列表，去除重复。
        LLM 结果优先（更准确），规则匹配做补充。
        """
        seen = set()
        merged = []

        # 先处理 LLM 结果（优先）
        for entity in llm_entities:
            key = (entity.get('cn_name', '') or '').lower().strip()
            if key and key not in seen:
                seen.add(key)
                # 也检查英文名
                en = (entity.get('en_name', '') or '').lower().strip()
                if en:
                    seen.add(en)
                merged.append(entity)

        # 再处理规则结果（补充 LLM 未找到的）
        for entity in rule_entities:
            cn_key = (entity.get('cn_name', '') or '').lower().strip()
            en_key = (entity.get('en_name', '') or '').lower().strip()

            if cn_key not in seen and en_key not in seen:
                if cn_key:
                    seen.add(cn_key)
                if en_key:
                    seen.add(en_key)
                merged.append(entity)

        return merged

    def _save_entities_and_create_tasks(self, entities: list, references: list) -> int:
        """
        将实体写入 skin_entities 表，并创建 skin_search_tasks。
        返回创建的任务数。
        """
        from db.skin_processor import SkinEntityProcessor, SkinSearchTaskProcessor

        tasks_created = 0

        with SkinEntityProcessor() as entity_proc:
            if not entity_proc.conn:
                logger.warning("[Parser] DB 连接失败，跳过持久化")
                return 0

            entity_proc.create_table_if_not_exists()

            with SkinSearchTaskProcessor() as task_proc:
                if not task_proc.conn:
                    logger.warning("[Parser] 任务表 DB 连接失败")
                    return 0

                task_proc.create_table_if_not_exists()

                for entity in entities:
                    cn_name = entity.get('cn_name')
                    if not cn_name:
                        continue

                    # 写入或更新 skin_entities
                    entity_id = entity_proc.upsert_skin_entity(
                        skin_name=cn_name,
                        market_hash_name=entity.get('en_name'),
                        weapon_type=entity.get('weapon_type'),
                    )

                    if entity_id is None:
                        continue

                    # 近期已有任务则跳过（避免重复调查）
                    if task_proc.has_recent_task(entity_id, hours=4):
                        continue

                    # 计算优先级
                    priority = self._calculate_priority(entity)

                    # 为每个来源引用创建任务（最多取前 3 条最相关的 reference）
                    relevant_refs = self._find_relevant_references(cn_name, references)[:3]

                    if relevant_refs:
                        for ref in relevant_refs:
                            task_id = task_proc.create_task(
                                skin_entity_id=entity_id,
                                source_url=ref.get('url'),
                                source_annotation_json=ref,
                                priority=priority,
                            )
                            if task_id:
                                tasks_created += 1
                    else:
                        # 无相关 reference，仍创建一个基础任务
                        task_id = task_proc.create_task(
                            skin_entity_id=entity_id,
                            source_url=None,
                            source_annotation_json=None,
                            priority=priority,
                        )
                        if task_id:
                            tasks_created += 1

        return tasks_created

    @staticmethod
    def _detect_weapon_type(weapon_name: str) -> str:
        """根据武器名称检测武器类型。"""
        weapon_lower = weapon_name.lower()
        for wtype, keywords in WEAPON_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in weapon_lower:
                    return wtype
        return "other"

    @staticmethod
    def _detect_price_event(text: str, entity_name: str) -> bool:
        """检测文本中是否有关于该实体的价格事件描述。"""
        # 寻找实体名称附近（100字符内）是否有价格事件关键词
        name_pos = text.lower().find(entity_name.lower())
        if name_pos == -1:
            return False
        context = text[max(0, name_pos - 100):name_pos + 200].lower()
        return any(kw.lower() in context for kw in PRICE_EVENT_KEYWORDS)

    @staticmethod
    def _calculate_priority(entity: dict) -> int:
        """
        计算任务优先级。
        3 = 价格事件（暴涨/暴跌）
        2 = 新皮肤发布
        1 = 一般提及
        """
        if entity.get('has_price_event'):
            event_type = entity.get('price_event_type', 'none')
            if event_type in ('surge', 'crash'):
                return 3
            elif event_type == 'new_release':
                return 2
        return 1

    @staticmethod
    def _find_relevant_references(entity_name: str, references: list) -> list:
        """
        从 references 列表中筛选提到该饰品名称的引用。
        """
        relevant = []
        entity_lower = entity_name.lower()
        for ref in references:
            combined = (
                (ref.get('title', '') or '') + ' ' +
                (ref.get('summary', '') or '')
            ).lower()
            if entity_lower in combined:
                relevant.append(ref)
        return relevant


def run_parser(scout_result: dict) -> dict:
    """便捷函数：运行 Parser Agent。"""
    agent = SkinParserAgent()
    return agent.parse(scout_result)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

    logging.basicConfig(level=logging.INFO)

    responses_dir = os.path.join(os.path.dirname(__file__), '..', 'responses')
    scout_files = sorted([
        f for f in os.listdir(responses_dir) if f.startswith('scout_')
    ]) if os.path.isdir(responses_dir) else []

    if not scout_files:
        logger.error("未找到 Scout 响应文件，请先运行 Scout Agent")
        sys.exit(1)

    test_file = os.path.join(responses_dir, scout_files[-1])
    with open(test_file, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    logger.info(f"使用 Scout 响应文件: {scout_files[-1]}")

    from llm.agents.scout_agent import ScoutAgent
    references = ScoutAgent._extract_references(raw)
    summary_text = ScoutAgent._extract_summary_text(raw)

    scout_result = {
        "response_data": raw,
        "references": references,
        "summary_text": summary_text,
    }

    agent = SkinParserAgent()
    result = agent.parse(scout_result)

    logger.info(f"提取到 {len(result['entities'])} 个饰品实体，创建了 {result['tasks_created']} 个调查任务")
