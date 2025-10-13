"""
Summarizer Agent
"""
from typing import Dict, Any
from llm.agents.base_agent import BaseAgent
from llm.clients.gemini_client import GeminiClient

class SummarizerAgent(BaseAgent):
    """Agent that summarizes the analysis from other agents."""

    def __init__(self, client: GeminiClient, temperature: float = 0.5):
        super().__init__(
            name="SummarizerAgent",
            role="报告摘要专家",
            client=client,
            temperature=temperature
        )

    def _build_system_instruction(self) -> str:
        """Builds the system instruction for the summarizer agent."""
        return (
            "你是一个专业的投资报告摘要专家。"
            "你的任务是接收多个分析报告，并将它们整合成一个连贯、精炼的投资摘要。"
            "摘要必须严格控制在200字以内，使用纯文本格式，采用自然段落叙述。"
            "不要使用 Markdown 标记、不要使用分点列表、不要使用特殊符号（如 ✅ ❌ 📊 等）。"
            "摘要必须包含：市场现状、主要风险与机会、明确的操作建议和策略。"
            "语言要专业、客观、精炼、易读，适合邮件阅读。"
        )

    def _build_summary_prompt(self, context: Dict[str, Any]) -> str:
        """Builds the prompt for generating the summary."""
        reports = []
        
        # Extract reports from different agents
        for agent_name, result in context.items():
            if agent_name == 'summary_agent':  # Skip self
                continue
            if isinstance(result, dict):
                # Try to get 'report' field first, then 'analysis'
                report_text = result.get('report') or result.get('analysis', '')
                if report_text:
                    reports.append(f"## {agent_name}:\n{report_text}\n")

        if not reports:
            return "没有可供摘要的分析报告。"

        full_report = "\n".join(reports)
        return (
            "请根据以下多个分析报告，生成一份不超过200字的纯文本投资摘要。\n\n"
            "格式要求：\n"
            "- 使用自然段落叙述，不要分点列表\n"
            "- 不要使用任何 Markdown 标记（如 **、#、- 等）\n"
            "- 不要使用 emoji 或特殊符号\n"
            "- 适合邮件正文阅读\n\n"
            "内容要求：\n"
            "- 第一段：市场现状和技术指标判断\n"
            "- 第二段：主要风险与机会分析\n"
            "- 第三段：操作建议和具体策略\n"
            "- 总字数严格控制在200字以内\n\n"
            f"--- 分析报告 ---\n{full_report}\n--- 结束 ---"
        )

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a summary of the analyses from other agents.

        Args:
            context: Dictionary containing the analysis results from other agents.

        Returns:
            Dictionary containing the summary.
        """
        prompt = self._build_summary_prompt(context)
        if prompt == "没有可供摘要的分析报告。":
            summary = "没有生成摘要，因为没有提供分析报告。"
        else:
            summary = self._generate_response(prompt)

        return {"summary": summary}
