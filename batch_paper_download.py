import os
import sys
import json
import requests
from datetime import datetime, timedelta
import subprocess
from tqdm import tqdm

def get_daily_papers(query_date):
    """获取指定日期的论文数据"""
    # 构建API URL
    url = f"https://hf-mirror.com/api/daily_papers?date={query_date}"
    print(f"请求API: {url}")
    
    try:
        # 发送GET请求
        response = requests.get(url, proxies={"http": None, "https": None})
        
        # 定义文件夹和文件名
        folder_name = 'Paper_metadata_download'
        file_name = f"{query_date}.json"
        
        # 创建文件夹（如果不存在）
        os.makedirs(folder_name, exist_ok=True)
        
        # 完整文件路径
        file_path = os.path.join(folder_name, file_name)
        
        if response.status_code == 200:
            # 检查是否有数据
            data = response.json()
            if data:
                # 如果返回的不是空列表
                print(f"在 {query_date} 找到数据.")
                # 写入数据到文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print(f"数据已写入文件 {file_path}")
                return True
            else:
                print(f"在 {query_date} 没有找到数据")
                # 写入1到文件以标记已检查但无数据
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(1, f)
                print(f"标记写入文件 {file_path}")
                return False
        else:
            print(f"请求失败，状态码：{response.status_code}")
            # 写入1到文件以标记已检查但请求失败
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(1, f)
            print(f"标记写入文件 {file_path}")
            return False
    except Exception as e:
        print(f"处理日期 {query_date} 时发生异常: {e}")
        return False

def process_date(date_str):
    """处理指定日期的数据"""
    print(f"\n========== 处理日期: {date_str} ==========")
    
    # 步骤1: 下载元数据
    success = get_daily_papers(date_str)
    if not success:
        print(f"日期 {date_str} 没有找到数据，跳过后续处理")
        return False
    
    # 步骤2: 处理数据 - 运行清洁脚本
    try:
        print("运行数据清洁脚本...")
        subprocess.run(["python", "HF-day-paper+GLMs-api-clean.py", date_str], check=True)
    except subprocess.CalledProcessError as e:
        print(f"运行清洁脚本时出错: {e}")
        return False
    
    # 步骤3: 处理数据 - 运行API调用脚本
    try:
        print("运行API调用脚本...")
        subprocess.run(["python", "HF-day-paper+GLMs-api.py", date_str], check=True)
    except subprocess.CalledProcessError as e:
        print(f"运行API调用脚本时出错: {e}")
        return False
    
    print(f"日期 {date_str} 处理完成")
    return True

def main():
    # 定义日期范围
    start_date = datetime.strptime("2025-05-21", "%Y-%m-%d")
    end_date = datetime.strptime("2025-07-01", "%Y-%m-%d")
    
    # 计算总天数用于进度条
    total_days = (end_date - start_date).days + 1
    
    # 创建日期列表
    date_range = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(total_days)]
    
    # 使用tqdm显示整体进度
    processed_count = 0
    skipped_count = 0
    
    for date_str in tqdm(date_range, desc="处理日期范围", unit="日"):
        success = process_date(date_str)
        if success:
            processed_count += 1
        else:
            skipped_count += 1
    
    print(f"\n批量处理完成!")
    print(f"总日期数: {total_days}")
    print(f"成功处理: {processed_count}")
    print(f"跳过日期: {skipped_count}")

if __name__ == "__main__":
    main() 