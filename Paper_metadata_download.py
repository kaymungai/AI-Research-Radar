import unittest
import requests
from datetime import datetime, timedelta, timezone
import json
import os
import subprocess
import sys

def run_script(script_name, date_param=None):
    if date_param:
        subprocess.run(["python", script_name, date_param])
    else:
        subprocess.run(["python", script_name])

class TestDailyPapers(unittest.TestCase):

    def setUp(self):
        # 检查是否有命令行参数提供日期
        if len(sys.argv) > 1 and sys.argv[1] not in ['-v', '--verbose']:
            self.query_date = sys.argv[1]
            print(f"使用指定的日期: {self.query_date}")
        else:
            # 获取当前日期和时间 (UTC 时间)
            self.current_date = datetime.now(timezone.utc)
            print(f"当前 UTC 日期和时间: {self.current_date}")

            # 将 UTC 时间转换为北京时间 (UTC+8)
            beijing_timezone = timezone(timedelta(hours=8))
            self.current_date_beijing = self.current_date.astimezone(beijing_timezone)
            print(f"当前北京时间和时间: {self.current_date_beijing}")

            # 计算查询的日期(前一天)
            self.query_date = (self.current_date_beijing - timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"使用昨天的日期: {self.query_date}")

        # 构建API URL
        self.url = f"https://hf-mirror.com/api/daily_papers?date={self.query_date}"
        print(f"API URL: {self.url}")

    def test_get_daily_papers(self):
        # 发送GET请求
        response = requests.get(self.url, proxies={"http": None, "https": None})

        # 定义文件夹和文件名
        folder_name = 'Paper_metadata_download'
        file_name = f"{self.query_date}.json"

        # 创建文件夹（如果不存在）
        os.makedirs(folder_name, exist_ok=True)

        # 完整文件路径
        file_path = os.path.join(folder_name, file_name)

        try:
            if response.status_code == 200:
                # 检查是否有数据
                data = response.json()
                if data:
                    # 如果返回的不是空列表
                    print(f"在 {self.query_date} 找到数据:")
                    print(data)
                    # 写入数据到文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    print(f"数据已写入文件 {file_path}")
                else:
                    print(f"在 {self.query_date} 没有找到数据")
                    # 写入1到文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(1, f)
                    print(f"1 已写入文件 {file_path}")
            else:
                print(f"请求失败，状态码：{response.status_code}")
                print(response.text)  # 打印出详细的错误信息
                # 写入1到文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(1, f)
                print(f"1 已写入文件 {file_path}")
        except Exception as e:
            print(f"写入文件时发生异常: {e}")
            self.fail(f"写入文件时发生异常: {e}")

if __name__ == '__main__':
    # 存储原始参数
    original_args = sys.argv.copy()
    
    # 仅保留第一个参数给unittest（如果存在）
    if len(sys.argv) > 1:
        query_date = sys.argv[1]
        sys.argv = [sys.argv[0]]  # 清除参数，避免unittest捕获
    else:
        query_date = None
    
    unittest.main(exit=False)
    
    # 如果有日期参数，传递给其他脚本
    if query_date:
        run_script("HF-day-paper+GLMs-api-clean.py", query_date)
        run_script("HF-day-paper+GLMs-api.py", query_date)
    else:
        run_script("HF-day-paper+GLMs-api-clean.py")
        run_script("HF-day-paper+GLMs-api.py")
    
    print("所有脚本执行完毕。")






