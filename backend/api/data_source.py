import json
import pymysql
import requests
import time
import threading
import csv
from tqdm import tqdm


class SteamDTDataSource:
    def __init__(self, config_path="config.json", api_keys_path="api-keys.txt"):
        # 读取配置文件
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # 读取 API keys
        with open(api_keys_path, "r", encoding="utf-8") as f:
            self.api_keys = [line.strip() for line in f if line.strip()]

        self.conn = None
        self.cursor = None

    def connect_db(self):
        self.conn = pymysql.connect(**self.config)
        self.cursor = self.conn.cursor()

    def disconnect_db(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def create_tables(self):
        # 创建 items 表
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
            marketHashName VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
            BUFF VARCHAR(100),
            C5 VARCHAR(100),
            HALOSKINS VARCHAR(100),
            YOUPIN VARCHAR(100)
        )
        """
        )

        # 创建 prices 表
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            marketHashName VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
            platform VARCHAR(50),
            platformItemId VARCHAR(100),
            sellPrice DECIMAL(10,2),
            sellCount INT,
            biddingPrice DECIMAL(10,2),
            biddingCount INT,
            updateTime BIGINT,
            UNIQUE KEY unique_market_platform (marketHashName, platform)
        )
        """
        )

    def import_items_from_csv(self, csv_path="items.csv"):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            # 计算总行数
            f.seek(0)
            total_lines = sum(1 for line in f) - 1
            f.seek(0)
            next(reader)  # 再次跳过表头
            for row in tqdm(reader, total=total_lines, desc="导入数据"):
                name, marketHashName, buff, c5, haloskins, youpin = row
                self.cursor.execute(
                    """
                INSERT INTO items (name, marketHashName, BUFF, C5, HALOSKINS, YOUPIN)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (name, marketHashName, buff, c5, haloskins, youpin),
                )
        self.conn.commit()

    def parse_json_to_csv(self, json_path="items.txt", csv_path="items.csv"):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data["data"]
        with open("items.json", "w", encoding="utf-8") as f:
            json.dump({"items": items}, f, ensure_ascii=False, indent=4)
        print("Successfully load items.json")

        # 读取 JSON 文件
        with open("items.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data["items"]
        platforms = ["BUFF", "C5", "HALOSKINS", "YOUPIN"]
        csv_data = []
        for item in items:
            row = {"name": item["name"], "marketHashName": item["marketHashName"]}
            for platform in platforms:
                row[platform] = ""
            for platform in item["platformList"]:
                if platform["name"] in platforms:
                    row[platform["name"]] = platform["itemId"]
            csv_data.append(row)

        # 写入 CSV 文件
        fieldnames = ["name", "marketHashName"] + platforms
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        print("see items.csv")

    def fetch_prices(self):
        # 查询所有 marketHashName，按 id 排序
        self.cursor.execute("SELECT marketHashName FROM items ORDER BY id")
        all_marketHashNames = [row[0] for row in self.cursor.fetchall()]

        # 分批，每批 100 个
        batch_size = 100
        batches = [
            all_marketHashNames[i : i + batch_size]
            for i in range(0, len(all_marketHashNames), batch_size)
        ]

        # 将批次分配给 API keys
        batches_for_keys = [
            batches[i :: len(self.api_keys)] for i in range(len(self.api_keys))
        ]

        # 进度条锁
        progress_lock = threading.Lock()
        progress_bar = tqdm(total=len(batches), desc="处理批次")

        def process_batches(my_batches, api_key):
            # 每个线程创建自己的连接
            conn = pymysql.connect(**self.config)
            cursor = conn.cursor()

            for batch in my_batches:
                # API 调用
                url = "https://open.steamdt.com/open/cs2/v1/price/batch"
                payload = json.dumps({"marketHashNames": batch})
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                }

                response = requests.post(url, headers=headers, data=payload)

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        data = result.get("data", [])
                        for item in data:
                            marketHashName = item["marketHashName"]
                            dataList = item["dataList"]
                            for price_data in dataList:
                                cursor.execute(
                                    """
                                INSERT INTO prices (marketHashName, platform, platformItemId, sellPrice, sellCount, biddingPrice, biddingCount, updateTime)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE
                                sellPrice = VALUES(sellPrice),
                                sellCount = VALUES(sellCount),
                                biddingPrice = VALUES(biddingPrice),
                                biddingCount = VALUES(biddingCount),
                                updateTime = VALUES(updateTime)
                                """,
                                    (
                                        marketHashName,
                                        price_data["platform"],
                                        price_data["platformItemId"],
                                        price_data["sellPrice"],
                                        price_data["sellCount"],
                                        price_data["biddingPrice"],
                                        price_data["biddingCount"],
                                        price_data["updateTime"],
                                    ),
                                )
                        conn.commit()
                    else:
                        print(f"API 调用失败: {result.get('errorMsg')}")
                else:
                    print(f"HTTP 错误: {response.status_code}")

                # 更新进度条
                with progress_lock:
                    progress_bar.update(1)

                # 休息 60 秒
                time.sleep(60)

            cursor.close()
            conn.close()

        # 启动线程
        threads = []
        for i, my_batches in enumerate(batches_for_keys):
            t = threading.Thread(
                target=process_batches, args=(my_batches, self.api_keys[i])
            )
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        progress_bar.close()

    def run_full_pipeline(self):
        self.connect_db()
        self.create_tables()
        self.parse_json_to_csv()
        self.import_items_from_csv()
        self.fetch_prices()
        self.disconnect_db()
        print("所有数据获取完成")


# 使用示例
if __name__ == "__main__":
    ds = SteamDTDataSource()
    ds.run_full_pipeline()
