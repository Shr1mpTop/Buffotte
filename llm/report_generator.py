"""
Report Generator

This module converts a Markdown report into various formats like HTML, PNG, and PDF.
"""
import os
from datetime import datetime
from typing import Dict
from markdown_it import MarkdownIt
from playwright.sync_api import sync_playwright
from weasyprint import HTML

class ReportGenerator:
    """Handles the conversion of Markdown reports to other formats."""

    def __init__(self, output_dir: str = 'models'):
        """
        Initializes the ReportGenerator.

        Args:
            output_dir: The directory to save the generated reports.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # Disable linkify to avoid requiring linkify-it-py dependency
        self.md = MarkdownIt("gfm-like").disable('linkify')

    def _md_to_html(self, markdown_content: str, title: str) -> str:
        """Converts Markdown content to a styled HTML string."""
        body = self.md.render(markdown_content)
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: sans-serif; margin: 40px; background-color: #fdfdfd; }}
        .report {{ max-width: 800px; margin: auto; padding: 30px; background-color: #ffffff; border: 1px solid #ddd; box-shadow: 0 0 10px rgba(0,0,0,0.05); }}
        h1, h2, h3 {{ color: #333; }}
        h1 {{ text-align: center; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        code {{ font-family: 'Courier New', Courier, monospace; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="report">
        <h1>{title}</h1>
        {body}
    </div>
</body>
</html>
"""
        return html

    def generate_png(self, markdown_content: str, filename_prefix: str) -> str:
        """
        Generates a PNG image from the Markdown report.

        Args:
            markdown_content: The Markdown report content.
            filename_prefix: The prefix for the output filename.

        Returns:
            The path to the generated PNG file.
        """
        title = "AI分析报告"
        html_content = self._md_to_html(markdown_content, title)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(self.output_dir, f"{filename_prefix}_{timestamp}.png")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_content)
            
            # Give some time for rendering
            page.wait_for_timeout(1000) 
            
            page.locator('.report').screenshot(path=output_path)
            browser.close()
            
        print(f"🖼️ PNG report generated at: {output_path}")
        return output_path

    def generate_pdf(self, markdown_content: str, filename_prefix: str) -> str:
        """
        Generates a PDF document from the Markdown report.

        Args:
            markdown_content: The Markdown report content.
            filename_prefix: The prefix for the output filename.

        Returns:
            The path to the generated PDF file.
        """
        title = "AI分析报告"
        html_content = self._md_to_html(markdown_content, title)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(self.output_dir, f"{filename_prefix}_{timestamp}.pdf")

        HTML(string=html_content).write_pdf(output_path)
        
        print(f"📄 PDF report generated at: {output_path}")
        return output_path

    def generate_all(self, markdown_content: str, filename_prefix: str = "ai_report") -> Dict[str, str]:
        """
        Generates all report formats (PNG and PDF).

        Args:
            markdown_content: The Markdown report content.
            filename_prefix: The prefix for the output filenames.

        Returns:
            A dictionary with paths to the generated files.
        """
        print("\n" + "="*60)
        print("📄 开始生成报告文件 (PNG, PDF)")
        print("="*60)
        
        png_path = self.generate_png(markdown_content, filename_prefix)
        pdf_path = self.generate_pdf(markdown_content, filename_prefix)
        
        print("\n✅ 所有报告文件生成完毕!")
        
        return {
            "png": png_path,
            "pdf": pdf_path
        }
