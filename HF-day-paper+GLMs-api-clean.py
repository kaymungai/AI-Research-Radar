# -*- coding: utf-8 -*-
import os
import json
import sys
from datetime import datetime, timedelta, timezone
from zhipuai import ZhipuAI

# 检查命令行参数
if len(sys.argv) > 1:
    # 如果提供了日期参数，使用该日期
    target_date_str = sys.argv[1]
    print(f"使用指定日期: {target_date_str}")
else:
    # 未提供日期，使用昨天的日期（保持原有功能）
    # 获取当前UTC时间
    current_utc_time = datetime.now(timezone.utc)
    print(f"当前 UTC 日期和时间: {current_utc_time}")

    # 将UTC时间转换为北京时间 (UTC+8)
    beijing_timezone = timezone(timedelta(hours=8))
    current_beijing_time = current_utc_time.astimezone(beijing_timezone)
    print(f"当前北京时间和时间: {current_beijing_time}")

    # 计算查询的日期(前一天)
    yesterday_beijing = current_beijing_time - timedelta(days=1)
    target_date_str = yesterday_beijing.strftime('%Y-%m-%d')
    print(f"使用昨天的日期: {target_date_str}")

# 文件名假设为 "YYYY-MM-DD.json"
filename = f"{target_date_str}.json"

# 搜索文件的根目录
root_directory = '.'

# 搜索文件
file_path = None
for dirpath, dirnames, filenames in os.walk(root_directory):
    if filename in filenames:
        file_path = os.path.join(dirpath, filename)
        break

if file_path:
    # 读取JSON文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    # 将文件内容转换为字符串
    user_content = json.dumps(data, ensure_ascii=False)
else:
    user_content = f"文件 {filename} 不存在"
    print(user_content)
    sys.exit(1)  # 如果文件不存在则退出

try:
    # 在环境变量中设置OPENAI_API_KEY为第一步拼接获得的API Key或者直接填写
    ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")

    client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
    # 调用对话补全接口
    result = client.chat.completions.create(
        # 必须填写您自己创建的智能体ID，否则无法调用成功
        model="GLM-4-Plus",
        # 目前多轮对话基于消息合并实现，某些场景可能导致能力下降且受单轮最大token数限制
        # 如果您想获得原生的多轮对话体验，可以传入首轮消息获得的id，来接续上下文
        # "conversation_id": "65f6c28546bae1f0fbb532de",
        messages=[
            {"role": "system", "content": "你是一个论文结构化助手，你的任务是将user部分的其他无关内容去除，只输出每篇文章的题目的中文翻译后的题目和每篇的id，格式如下,每行都要换行。根据您的要求，以下是论文的题目中文翻译和ID：\n\n1. 论文题目：'此处填写论文的题目'\n   中文翻译：'此处填写翻译为中文的论文题目'\n   论文ID：'此处填写论文的ID'\n\n。请遵循以上格式给我返回数据，如果无法查询到，请重试查询三次。"},
            {"role": "user", "content": user_content},
        ],
        # 如果使用SSE流请设置为true，默认false
        stream=False
    )

    # 初始化用于保存结果的列表
    structured_data = []
    for choice in result.choices:
        structured_data.append(choice.message.content)

    # 创建保存文件夹
    output_folder = 'HF-day-paper+GLMs-api-clean'
    os.makedirs(output_folder, exist_ok=True)

    # 生成新的文件名并保存到指定文件夹
    clean_filename = os.path.join(output_folder, f"{target_date_str}_clean.json")

    # 将结构化数据写入新的JSON文件
    with open(clean_filename, 'w', encoding='utf-8') as clean_file:
        json.dump(structured_data, clean_file, ensure_ascii=False, indent=4)

    print(f"结构化数据已保存到 {clean_filename}")
    sys.exit(0)  # 成功完成

except ValueError as e:
    print(f"发生错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"发生异常: {e}")
    sys.exit(1)









