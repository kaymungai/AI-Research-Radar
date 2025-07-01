# -*- coding: utf-8 -*-
import os
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from zhipuai import ZhipuAI
from tqdm import tqdm

# 配置zhipuai API
ZHIPUAI_API_KEY = ZHIPUAI_API_KEY = os.environ.get("ZHIPUAI_API_KEY")

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)

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

# 搜索包含指定日期的JSON文件
def find_files_with_date(search_path, date_str):
    result = []
    for root, dirs, files in os.walk(search_path):
        for file in files:
            if date_str in file and file.endswith('.json'):
                result.append(os.path.join(root, file))
    return result

# 设置搜索路径为当前项目根目录
search_path = '.'

# 查找包含指定日期的JSON文件
json_files = find_files_with_date(search_path, target_date_str)
if not json_files:
    print(f"未找到包含日期\"{target_date_str}\"的JSON文件。")
    sys.exit(1)
else:
    print(f"找到以下文件：{json_files}")

# 矫正文件内容
def correct_json_content(data):
    if isinstance(data, list):
        # 将列表中的元素拼接成一个完整的字符串
        return ''.join(data)
    return data

# 提取ID并生成URL
def extract_ids(corrected_data):
    # 使用正则表达式提取ID
    ids = re.findall(r'\d{4}\.\d{5}', corrected_data)
    return ids

# 提取提取中文翻译
def extract_titles(corrected_data):
    # 使用正则表达式提取ID
    ititles = re.findall(r'论文题目：(.*?)\n\s*', corrected_data)
    return ititles

# 提取中文翻译题目
def extract_translations(corrected_data):
    # 使用正则表达式提取ID
    translations = re.findall(r'中文翻译：(.*?)\n\s*', corrected_data)
    return translations

# 处理找到的JSON文件并保存结果
results = []

for file_path in json_files:
    print(f"找到文件：{file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            corrected_data = correct_json_content(data)
            print(f"矫正后的文件内容：\n{corrected_data}")
            
            # 提取ID并生成URL
            ids = extract_ids(corrected_data)
            # 提取提取中文翻译
            ititles = extract_titles(corrected_data)
            # 提取中文翻译题目
            translations = extract_translations(corrected_data)
            
            print(f"ids: {ids}")
            print(f"ititles: {ititles}")
            print(f"translations: {translations}")

            # 裁剪三者为最小长度，保证后续处理一致
            min_len = min(len(ids), len(ititles), len(translations))
            ids = ids[:min_len]
            ititles = ititles[:min_len]
            translations = translations[:min_len]

            # 检查是否有有效的数据可处理
            if not ids or not ititles or not translations or len(ids) != len(ititles) or len(ids) != len(translations):
                print(f"文件 {file_path} 中没有有效的数据或数据不完整，跳过处理")
                continue

            # 使用tqdm显示进度条 
            for index, arxiv_id in tqdm(enumerate(ids),desc=f"Processing {file_path}", unit="id", total=len(ids)):
                url = f"https://arxiv.org/abs/{arxiv_id}"
                ititlesNow = ititles[index]
                translationsNow = translations[index]
                print(f"Arxiv URL: {url},{ititlesNow},{translationsNow}")
                # 调用OpenAI API处理URL
                result = client.chat.completions.create(
                    model="GLM-4-AirX",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"你是一个文章总结大师，你非常擅长总结，下面我会给你提供文章URL地址，你根据我的URL地址来总结这篇文章的内容。按以下三部分格式生成，这三部分每个单独为一行,当前的标题和中文文章标题要和我给你的文章的URL对应，不要有错。文章标题《{ititlesNow}》，\n   中文文章标题《{translationsNow}》，\n   文章内容：['此处填写翻译中文后的文章内容，精简总结50字以内']\n   请牢记住我上面说的内容，严格执行，不要进行多余的操作和想法。现在我要告诉你我的文章的URL是：{url}"
                                }
                            ]
                        }
                    ],
                    stream=False
                )
                
                # 输出调用结果
                print(result.choices[0].message.content)
                
                # 保存结果到列表中
                # 模型论文地址部分
                results.append([{"tag": "text", "text": "模型论文地址：", "style": ["bold"]},
                                {"tag": "text", "text": url}])
                # 模型概述部分
                results.append([{"tag": "text", "text": "模型概述：", "style": ["bold"]},
                                {"tag": "text", "text": result.choices[0].message.content}])
                # 添加分隔线
                results.append([{"tag": "hr"}])
    except Exception as e:
        print(f"无法读取或处理文件 {file_path}：{e}")
        continue

# 如果没有成功处理任何数据，提前退出
if not results:
    print("没有成功处理任何数据，退出")
    sys.exit(1)

# 创建保存文件夹
output_folder = 'HF-day-paper+GLMs-api'
os.makedirs(output_folder, exist_ok=True)

# 保存结果到JSON文件
output_file = os.path.join(output_folder, f"{target_date_str}_HF_glms_api_clean.json")
with open(output_file, 'w', encoding='utf-8') as outfile:
    json.dump(results, outfile, ensure_ascii=False, indent=4)

print(f"结果已保存到文件：{output_file}")
sys.exit(0)









