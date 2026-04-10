import logging
import os
import pymysql
import pytz
from datetime import datetime, date
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class MarketAnalysisProcessor:
    def __init__(self):
        self.config = {
            'host': os.getenv('HOST'),
            'port': int(os.getenv('PORT', 3306)),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DATABASE'),
            'charset': os.getenv('CHARSET', 'utf8mb4')
        }

    def get_db_connection(self):
        return pymysql.connect(**self.config)

    def create_table(self):
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS market_analysis (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        analysis TEXT NOT NULL,
                        analysis_date DATE UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    COMMENT='每日大盘分析'
                """)
            conn.commit()
            logger.info("表 'market_analysis' 创建成功或已存在。")
        except Exception as e:
            logger.error(f"创建表失败: {e}")
        finally:
            if conn:
                conn.close()

    def get_recent_kline_data(self, days=30):
        """从 kline_data_day 获取近 N 天数据用于分析。"""
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT date, open_price, high_price, low_price, close_price, volume, turnover
                    FROM kline_data_day
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (days,))
                rows = cursor.fetchall()
                return list(reversed(rows))
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_prediction_data(self, days=7):
        """获取未来预测数据。"""
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                today = date.today()
                cursor.execute("""
                    SELECT date, predicted_close_price, rolling_std_7
                    FROM kline_data_prediction
                    WHERE date >= %s
                    ORDER BY date
                    LIMIT %s
                """, (today, days))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取预测数据失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def build_prompt(self, kline_data, prediction_data):
        """构造发送给 LLM 的 prompt。"""
        lines = []
        lines.append("你是 CS2 饰品大盘市场分析师。请根据以下数据分析今日大盘形势，对比近期数据并给出简短预判。")
        lines.append("要求：1. 语言通俗易懂，不要术语堆砌；2. 总字数 150-250 字；3. 分为'今日行情'、'趋势对比'、'短期预判'三段。")
        lines.append("")

        if kline_data:
            latest = kline_data[-1]
            lines.append(f"【最新数据】日期: {latest['date']}, 开盘: {latest['open_price']}, "
                         f"收盘: {latest['close_price']}, 最高: {latest['high_price']}, "
                         f"最低: {latest['low_price']}, 成交量: {latest['volume']}, 成交额: {latest['turnover']}")

            if len(kline_data) >= 2:
                prev = kline_data[-2]
                change_pct = (float(latest['close_price']) - float(prev['close_price'])) / float(prev['close_price']) * 100
                lines.append(f"【对比昨日】涨跌幅: {change_pct:+.2f}%")

            lines.append(f"【近{len(kline_data)}日概况】")
            closes = [float(r['close_price']) for r in kline_data]
            volumes = [r['volume'] for r in kline_data]
            lines.append(f"  价格区间: {min(closes):.2f} ~ {max(closes):.2f}")
            lines.append(f"  平均收盘价: {sum(closes)/len(closes):.2f}")
            lines.append(f"  平均成交量: {sum(volumes)//len(volumes)}")

            # 最近7天 vs 之前7天对比
            if len(kline_data) >= 14:
                recent_avg = sum(closes[-7:]) / 7
                prev_avg = sum(closes[-14:-7]) / 7
                diff_pct = (recent_avg - prev_avg) / prev_avg * 100
                lines.append(f"  近7日均价 vs 前7日均价: {diff_pct:+.2f}%")

        if prediction_data:
            lines.append(f"【模型预测】")
            for p in prediction_data[:5]:
                lines.append(f"  {p['date']}: 预测 {float(p['predicted_close_price']):.2f}")

        return "\n".join(lines)

    def generate_analysis(self):
        """主流程：获取数据 → 调用 LLM → 存入数据库。"""
        self.create_table()

        kline_data = self.get_recent_kline_data(30)
        if not kline_data:
            logger.error("无K线数据，跳过分析生成。")
            return False

        prediction_data = self.get_prediction_data(7)
        prompt = self.build_prompt(kline_data, prediction_data)

        logger.info(f"Prompt 长度: {len(prompt)} 字符")
        logger.info("正在调用豆包 LLM 生成分析...")

        try:
            import httpx
            api_key = os.getenv("ARK_API_KEY")
            model = os.getenv("DOUBAO_MODEL", "doubao-seed-1-6-flash-250828").strip("[]").split(",")[-1]
            base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

            if not api_key:
                logger.error("ARK_API_KEY 未设置")
                return False

            response = httpx.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7,
                },
                timeout=30.0,
            )
            result = response.json()
            if "choices" not in result:
                logger.error(f"LLM 返回异常: {response.status_code} {result}")
                return False
            analysis_text = result["choices"][0]["message"]["content"]
            logger.info(f"LLM 返回分析: {analysis_text[:100]}...")
        except Exception as e:
            logger.error(f"调用 LLM 失败: {e}")
            return False

        return self.save_analysis(analysis_text)

    def save_analysis(self, text):
        """将分析文本存入数据库。"""
        conn = None
        try:
            conn = self.get_db_connection()
            today = datetime.now(pytz.timezone('Asia/Shanghai')).date()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO market_analysis (analysis, analysis_date)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE analysis = VALUES(analysis), created_at = CURRENT_TIMESTAMP
                """, (text, today))
            conn.commit()
            logger.info(f"市场分析已保存: {today}")
            return True
        except Exception as e:
            logger.error(f"保存分析失败: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_latest_analysis(self):
        """获取最新的市场分析。"""
        conn = None
        try:
            conn = self.get_db_connection()
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT id, analysis, analysis_date, created_at
                    FROM market_analysis
                    ORDER BY analysis_date DESC
                    LIMIT 1
                """)
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"获取分析失败: {e}")
            return None
        finally:
            if conn:
                conn.close()


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    processor = MarketAnalysisProcessor()
    success = processor.generate_analysis()
    if success:
        logger.info("市场分析生成完成。")
    else:
        logger.error("市场分析生成失败。")


if __name__ == "__main__":
    main()
