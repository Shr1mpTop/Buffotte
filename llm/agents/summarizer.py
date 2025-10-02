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
            "你是一个专业的报告摘要专家。"
            "你的任务是接收多个分析报告，并将它们整合成一个连贯、精炼的摘要。"
            "摘要必须严格控制在200字以内，语言要专业、客观、精炼。"
            "你的输出只能包含摘要内容，不能有任何多余的解释或标题。"
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
            "请根据以下多个分析报告，生成一份不超过200字的综合摘要。\n\n"
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
