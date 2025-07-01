import os
import sys
import json
import logging
from typing import List, Dict, Any

# =====================
# 日志配置
# =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def find_json_files(input_path: str) -> List[str]:
    """
    查找指定路径下所有 *_HF_glms_api_clean.json 文件。
    支持目录递归和单文件。
    """
    json_files = []
    if os.path.isfile(input_path):
        if input_path.endswith('_HF_glms_api_clean.json'):
            json_files.append(input_path)
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file in files:
                if file.endswith('_HF_glms_api_clean.json'):
                    json_files.append(os.path.join(root, file))
    else:
        logger.error(f"输入路径无效: {input_path}")
    return json_files


def split_json_to_models(json_path: str) -> List[Dict[str, Any]]:
    """
    优化分割算法，确保每个模型严格由“模型论文地址”组和“模型概述”组组成。
    只提取“中文文章标题”或“文章标题”作为md文件名。
    """
    import re
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 只保留tag为text且text内容为“模型论文地址：”或“模型概述：”的数组索引
    model_indices = []
    for idx, arr in enumerate(data):
        if isinstance(arr, list) and len(arr) > 0 and arr[0].get('tag') == 'text':
            first_text = arr[0].get('text', '')
            if first_text.strip() in ('模型论文地址：', '模型概述：'):
                model_indices.append(idx)

    # 每2个索引为一组，严格分组
    model_infos = []
    for i in range(0, len(model_indices), 2):
        if i+1 >= len(model_indices):
            logger.warning(f"模型分组不完整，跳过: {json_path} 第{i//2}组")
            continue
        group1 = data[model_indices[i]]
        group2 = data[model_indices[i+1]]
        # 取group1的第二个对象text为论文地址
        paper_url = ''
        if len(group1) > 1 and group1[1].get('tag') == 'text':
            paper_url = group1[1].get('text', '')
        elif group1:
            paper_url = group1[0].get('text', '')
        # 取group2的第二个对象text为模型概述
        overview = ''
        if len(group2) > 1 and group2[1].get('tag') == 'text':
            overview = group2[1].get('text', '')
        elif group2:
            overview = group2[0].get('text', '')
        # 只提取“中文文章标题”或“文章标题”作为md文件名
        chinese_title = ''
        m = re.search(r'中文文章标题[：: ]*(《.*?》|[^\n\r，。；：:]+)', overview)
        if m:
            chinese_title = m.group(1).strip()
        else:
            m2 = re.search(r'标题[：: ]*(《.*?》|[^\n\r，。；：:]+)', overview)
            if m2:
                chinese_title = m2.group(1).strip()
        if not chinese_title:
            arxiv_id = paper_url.split('/')[-1] if paper_url else 'unknown'
            short_overview = overview[:10].replace('\n', '').replace(' ', '')
            chinese_title = f'{arxiv_id}_{short_overview}'
            logger.info(f"未找到中文文章标题或文章标题，自动生成: {chinese_title}")
        model_infos.append({
            'paper_url': paper_url,
            'overview': overview,
            'chinese_title': chinese_title
        })
    return model_infos


def write_models_to_md(models: List[Dict[str, Any]], json_path: str):
    """
    将模型信息写入md文件，按json文件名中的日期创建目录，文件名用中文标题。
    文件名做合法化处理，防止写入失败。
    """
    import re
    # 文件名合法化处理
    def safe_filename(name, maxlen=60):
        name = re.sub(r'[\\/:*?"<>|\n\r]', '_', name)
        name = name.strip()
        if len(name) > maxlen:
            name = name[:maxlen]
        return name
    # 从json文件名中提取日期（如2025-05-16）
    basename = os.path.basename(json_path)
    m = re.match(r'(\d{4}-\d{2}-\d{2})', basename)
    if not m:
        logger.error(f"文件名未包含日期，跳过: {json_path}")
        return
    date_dir = m.group(1)
    if not os.path.exists(date_dir):
        os.makedirs(date_dir)
        logger.info(f"创建目录: {date_dir}")
    for model in models:
        # 文件名用中文标题，做合法化处理
        title = model['chinese_title']
        safe_title = safe_filename(title)
        md_path = os.path.join(date_dir, f"{safe_title}.md")
        content = f"模型论文地址：{model['paper_url']}\n\n模型概述：{model['overview']}\n"
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"写入: {md_path}")
        except Exception as e:
            logger.error(f"写入失败: {md_path}，原因: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='批量将HF GLMs API JSON切分为MD文件')
    parser.add_argument('input_path', help='输入目录或单个json文件路径')
    args = parser.parse_args()

    json_files = find_json_files(args.input_path)
    if not json_files:
        logger.error('未找到任何 *_HF_glms_api_clean.json 文件')
        sys.exit(1)

    for json_file in json_files:
        logger.info(f"处理文件: {json_file}")
        models = split_json_to_models(json_file)
        write_models_to_md(models, json_file)

if __name__ == '__main__':
    main() 