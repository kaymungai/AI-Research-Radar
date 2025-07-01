import os
import re
import subprocess
import sys

# 判断目录名是否为yyyy-mm-dd格式
def is_date_dir(dirname):
    return re.match(r'^\d{4}-\d{2}-\d{2}$', dirname) is not None

def main():
    if len(sys.argv) < 2:
        print("用法: python batch_classify_md.py <input_path> <knowledge_path>")
        print("如果 <input_path> 为 ./ ，则自动批量处理所有日期目录")
        sys.exit(1)

    input_path = sys.argv[1]
    knowledge_path = sys.argv[2] if len(sys.argv) > 2 else None

    if input_path == './':
        # 批量处理所有日期目录
        root = os.path.abspath('.')
        all_dirs = [d for d in os.listdir(root) if os.path.isdir(d) and is_date_dir(d)]
        all_dirs.sort()
        print(f"检测到日期目录: {all_dirs}")
        for date_dir in all_dirs:
            print(f"处理目录: {date_dir}")
            cmd = [
                sys.executable,  # 当前python解释器
                "classify_and_generate_mdDouBao.py",
                date_dir,
                knowledge_path
            ]
            result = subprocess.run(cmd)
            if result.returncode != 0:
                print(f"处理 {date_dir} 失败，返回码: {result.returncode}")
    else:
        # 兼容原有单目录处理
        cmd = [
            sys.executable,
            "classify_and_generate_mdDouBao.py",
            input_path,
            knowledge_path
        ]
        subprocess.run(cmd)

if __name__ == "__main__":
    main() 