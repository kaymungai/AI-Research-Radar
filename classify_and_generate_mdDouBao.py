import os
import sys
import json
import logging
from typing import List
from volcenginesdkarkruntime import Ark  # 替换zhipuai为Ark
from tqdm import tqdm

# ========== 日志配置 ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ========== 配置Ark API ==========
# Ark API Key需通过环境变量 ARK_API_KEY 提供
client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.environ.get("ARK_API_KEY"),
)

# ========== 工具函数 ==========
def find_md_files(input_path: str) -> List[str]:
    """
    查找指定路径下所有.md文件，支持目录递归和单文件。
    """
    md_files = []
    if os.path.isfile(input_path):
        if input_path.endswith('.md'):
            md_files.append(input_path)
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file in files:
                if file.endswith('.md'):
                    md_files.append(os.path.join(root, file))
    else:
        logger.error(f"输入路径无效: {input_path}")
    return md_files

# ========== 主处理函数 ==========
def classify_and_generate_md(md_path: str, knowledge_path: str):
    """
    读取知识库和md内容，调用方舟Ark，返回分类和新md内容，并写入新目录。
    """
    # 读取知识库内容
    with open(knowledge_path, 'r', encoding='utf-8') as f:
        knowledge = f.read()
    # 读取md内容
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    # 构造prompt
    prompt = f"""
你是一个AI模型分类与总结专家，并且可以访问互联网的链接地址。请根据下面的“模型分类知识库”内容，判断下方md文件描述的模型属于哪个分类，并用如下md格式输出：
# [此处填当前模型md文件对应知识库中的分类名，不用包含[]符号]

# [模型名称] - [arXiv 标题]

**模型功能**：
[请访问下方md内容中的模型论文地址:，结合论文实际内容，总结模型的主要功能]

**arXiv 文章链接**：
[arXiv 链接](https://arxiv.org/abs/XXXX)

**作者/团队**：
[请访问下方md内容中的模型论文地址：，总结作者姓名或团队名称]

**发表日期**：
[请访问下方md内容中的模型论文地址：，总结论文的首次提交或发表日期]

**研究进展**：
[请访问下方md内容中的模型论文地址：，结合论文摘要和主要内容，总结该模型的研究进展和创新点]

**应用场景**：
[请访问下方md内容中的模型论文地址：，结合论文内容，总结该模型的典型应用场景]

请严格按上述md格式输出。所有字段（模型名称、arXiv标题、链接、作者、日期、研究进展、应用场景）必须访问下方md内容中的模型论文地址（arXiv链接），从论文页面获取、总结和翻译相关内容后填充，不能只依赖知识库和md文件内容，不能输出“待补充”，空内容，无法访问论文页面，待访问论文页面，待补充这些懒惰行为，你必须马上访问执行访问论文页面。请确保访问模型论文地址后，可以获取到相关内容。请确保所有字段都与论文实际内容高度相关。

【模型分类知识库】:
{knowledge}

【模型md文件内容】:
{md_content}


"""
    # 调用方舟Ark
    result = client.chat.completions.create(
        model="doubao-1-5-pro-32k-250115",  # 替换为Ark模型ID
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        stream=False
    )
    # 解析返回内容
    content = result.choices[0].message.content.strip()
    # 期望返回：第一行为分类，后面为md内容
    lines = content.split('\n')
    category = lines[0].strip().replace('#', '').replace('：', '').replace(':', '').strip()
    new_md = '\n'.join(lines[1:]).strip()
    return category, new_md

# ========== 主入口 ==========
def main():
    import argparse
    parser = argparse.ArgumentParser(description='根据知识库对模型md文件分类并生成新md文件')
    parser.add_argument('input_path', help='输入目录或单个md文件路径')
    parser.add_argument('knowledge_path', help='知识库txt或md文件路径')
    args = parser.parse_args()

    md_files = find_md_files(args.input_path)
    if not md_files:
        logger.error('未找到任何md文件')
        sys.exit(1)

    for md_file in tqdm(md_files, desc='批量处理md文件'):
        logger.info(f"处理文件: {md_file}")
        try:
            category, new_md = classify_and_generate_md(md_file, args.knowledge_path)
            # 取日期目录（假设md文件在如2025-05-20/xxx.md）
            date_dir = os.path.dirname(md_file)
            # 在日期目录下新建分类目录
            category_dir = os.path.join(date_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            # 新md文件名与原md一致
            md_basename = os.path.basename(md_file)
            new_md_path = os.path.join(category_dir, md_basename)
            with open(new_md_path, 'w', encoding='utf-8') as f:
                f.write(new_md)
            logger.info(f"写入: {new_md_path}")
        except Exception as e:
            logger.error(f"处理失败: {md_file}，原因: {e}")

if __name__ == '__main__':
    main() 