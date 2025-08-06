#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def find_common_words(file1_path, file2_path, output_path):
    """
    找到两个txt文件中相同的单词，并输出到新文件
    输出顺序与file1.txt中的顺序保持一致

    参数:
    file1_path: 第一个文件路径
    file2_path: 第二个文件路径
    output_path: 输出文件路径
    """

    try:
        # 读取第一个文件中的单词，保持顺序
        words1_list = []
        with open(file1_path, 'r', encoding='utf-8') as f1:
            for line in f1:
                word = line.strip()
                if word:  # 忽略空行
                    words1_list.append(word)

        # 读取第二个文件中的单词到集合中
        with open(file2_path, 'r', encoding='utf-8') as f2:
            words2_set = set(line.strip() for line in f2 if line.strip())

        # 按file1的顺序找出相同的单词，并去重
        common_words = []
        seen = set()  # 用于去重

        for word in words1_list:
            if word in words2_set and word not in seen:
                common_words.append(word)
                seen.add(word)

        # 将相同的单词按file1的顺序写入输出文件
        with open(output_path, 'w', encoding='utf-8') as output_file:
            for word in common_words:
                output_file.write(word + '\n')

        print(f"找到 {len(common_words)} 个相同单词")
        print(f"结果已保存到: {output_path}")

        return len(common_words)

    except FileNotFoundError as e:
        print(f"文件未找到: {e}")
        return -1
    except Exception as e:
        print(f"发生错误: {e}")
        return -1


def main():
    # 文件路径设置
    file1_path = "file1.txt"
    file2_path = "file2.txt"
    output_path = "common_words.txt"

    # 执行查找
    result = find_common_words(file1_path, file2_path, output_path)

    if result >= 0:
        print("处理完成!")
    else:
        print("处理失败!")


if __name__ == "__main__":
    main()
