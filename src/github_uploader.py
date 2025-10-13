"""
GitHub API 文件上传工具

用于将生成的预测图上传到 GitHub 图床仓库。
"""
import os
import json
import base64
import requests
from datetime import datetime


class GitHubUploader:
    """GitHub API 文件上传器"""

    def __init__(self, token: str, repo_owner: str, repo_name: str):
        """
        初始化上传器

        Args:
            token: GitHub Personal Access Token
            repo_owner: 仓库所有者 (如: Shr1mpTop)
            repo_name: 仓库名称 (如: picgo-images)
        """
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_file_sha(self, folder_path: str) -> str:
        """
        获取文件的 SHA 值（用于更新已存在的文件）

        Args:
            folder_path: 仓库中的文件路径

        Returns:
            文件的 SHA 值，如果文件不存在返回 None
        """
        try:
            response = requests.get(
                f"{self.base_url}/{folder_path}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()['sha']
            return None
        except Exception as e:
            print(f"获取文件 SHA 时出错: {e}")
            return None

    def upload_file(self, file_path: str, folder_path: str, commit_message: str = "Upload prediction chart") -> str:
        """
        上传文件到 GitHub 仓库

        Args:
            file_path: 本地文件路径
            folder_path: 仓库中的文件夹路径 (如: buffotte-kline-predictions/kline_pred_20251012.png)
            commit_message: 提交信息

        Returns:
            文件的公网URL
        """
        try:
            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Base64 编码
            encoded_content = base64.b64encode(file_content).decode('utf-8')

            # 检查文件是否已存在，如果存在则获取其 SHA
            existing_sha = self.get_file_sha(folder_path)

            # 构建请求数据
            data = {
                "message": commit_message,
                "content": encoded_content
            }

            # 如果文件已存在，添加 sha 参数
            if existing_sha:
                data["sha"] = existing_sha
                print(f"文件已存在，将更新现有文件 (SHA: {existing_sha[:7]}...)")

            # 发送请求
            response = requests.put(
                f"{self.base_url}/{folder_path}",
                headers=self.headers,
                json=data
            )

            if response.status_code in [200, 201]:
                # 上传成功（201=创建，200=更新），返回文件URL
                result = response.json()
                return result['content']['download_url']
            else:
                print(f"上传失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"上传过程中出错: {e}")
            return None


def upload_prediction_chart(local_path: str, date_str: str, token: str) -> str:
    """
    上传预测图表到 GitHub 图床

    Args:
        local_path: 本地图片路径
        date_str: 日期字符串 (YYYYMMDD格式)
        token: GitHub token

    Returns:
        图片的公网URL，如果上传失败返回None
    """
    uploader = GitHubUploader(
        token=token,
        repo_owner="Shr1mpTop",
        repo_name="picgo-images"
    )

    # 构建仓库中的文件路径
    folder_path = f"buffotte-kline-predictions/kline_pred_{date_str}.png"

    # 上传文件
    url = uploader.upload_file(
        file_path=local_path,
        folder_path=folder_path,
        commit_message=f"Upload K-line prediction chart for {date_str}"
    )

    if url:
        print(f"✅ 预测图已上传到: {url}")
    else:
        print("❌ 预测图上传失败")

    return url