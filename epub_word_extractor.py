#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB单词书提取器（支持页码范围）
从EPUB格式的单词书中提取指定页码范围的英文单词，去重后保存为TXT文件
"""

import os
import re
import sys
import zipfile
import argparse
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET


def get_epub_spine(epub_file_path):
    """
    获取EPUB的spine（阅读顺序），返回有序的内容文件列表
    """
    try:
        with zipfile.ZipFile(epub_file_path, 'r') as epub_zip:
            # 查找container.xml获取OPF文件位置
            container_path = 'META-INF/container.xml'
            if container_path in epub_zip.namelist():
                with epub_zip.open(container_path) as container_file:
                    container_content = container_file.read().decode('utf-8', errors='ignore')
                    opf_match = re.search(
                        r'full-path="([^"]+\.opf)"', container_content)
                    if opf_match:
                        opf_path = opf_match.group(1)
                    else:
                        # 备用方案：查找OPF文件
                        opf_files = [
                            f for f in epub_zip.namelist() if f.endswith('.opf')]
                        if not opf_files:
                            return []
                        opf_path = opf_files[0]
            else:
                # 备用方案：直接查找OPF文件
                opf_files = [f for f in epub_zip.namelist()
                             if f.endswith('.opf')]
                if not opf_files:
                    return []
                opf_path = opf_files[0]

            # 解析OPF文件获取spine
            with epub_zip.open(opf_path) as opf_file:
                opf_content = opf_file.read().decode('utf-8', errors='ignore')

                # 解析manifest（文件映射）
                manifest = {}
                manifest_matches = re.findall(
                    r'<item[^>]+id="([^"]+)"[^>]+href="([^"]+)"', opf_content)
                opf_dir = os.path.dirname(opf_path)

                for item_id, href in manifest_matches:
                    # 构建完整路径
                    if opf_dir:
                        full_path = os.path.join(
                            opf_dir, href).replace('\\', '/')
                    else:
                        full_path = href
                    manifest[item_id] = full_path

                # 解析spine（阅读顺序）
                spine_matches = re.findall(
                    r'<itemref[^>]+idref="([^"]+)"', opf_content)

                # 根据spine顺序构建文件列表
                ordered_files = []
                for item_id in spine_matches:
                    if item_id in manifest:
                        file_path = manifest[item_id]
                        # 只包含HTML/XHTML文件
                        if file_path.lower().endswith(('.html', '.xhtml', '.htm')):
                            ordered_files.append(file_path)

                return ordered_files

    except Exception as e:
        print(f"获取EPUB结构时出错: {e}")
        return []


def extract_epub_content_by_range(epub_file_path, start_page=None, end_page=None):
    """
    提取EPUB文件指定范围的内容
    """
    try:
        # 获取有序的内容文件列表
        ordered_files = get_epub_spine(epub_file_path)

        if not ordered_files:
            print("警告: 无法获取EPUB结构，将提取所有HTML文件")
            # 备用方案：提取所有HTML文件
            with zipfile.ZipFile(epub_file_path, 'r') as epub_zip:
                ordered_files = [f for f in epub_zip.namelist()
                                 if f.endswith(('.html', '.xhtml', '.htm')) and
                                 not f.startswith('META-INF/')]

        total_files = len(ordered_files)
        print(f"找到 {total_files} 个内容文件")

        # 确定要处理的文件范围
        if start_page is None:
            start_idx = 0
        else:
            start_idx = max(0, start_page - 1)  # 转换为0基索引

        if end_page is None:
            end_idx = total_files
        else:
            end_idx = min(total_files, end_page)

        if start_idx >= total_files:
            print(f"错误: 起始页码 {start_page} 超出范围（总共 {total_files} 个文件）")
            return ""

        files_to_process = ordered_files[start_idx:end_idx]
        print(
            f"将处理第 {start_idx + 1} 到第 {end_idx} 个文件（共 {len(files_to_process)} 个文件）")

        extracted_content = ""

        with zipfile.ZipFile(epub_file_path, 'r') as epub_zip:
            for i, file_name in enumerate(files_to_process, start_idx + 1):
                try:
                    if file_name in epub_zip.namelist():
                        with epub_zip.open(file_name) as content_file:
                            content = content_file.read().decode('utf-8', errors='ignore')
                            extracted_content += content + "\n"
                        print(
                            f"  处理文件 {i}/{total_files}: {os.path.basename(file_name)}")
                    else:
                        print(f"  警告: 文件 {file_name} 不存在")
                except Exception as e:
                    print(f"  读取文件 {file_name} 时出错: {e}")
                    continue

        return extracted_content

    except zipfile.BadZipFile:
        print("错误: 不是有效的EPUB文件（ZIP格式损坏）")
        return ""
    except Exception as e:
        print(f"提取EPUB内容时出错: {e}")
        return ""


def extract_english_words(content):
    """
    提取英文单词
    """
    # 使用正则表达式匹配英文单词
    # 匹配由字母组成的单词，可以包含连字符和撇号
    word_pattern = r'\b[a-zA-Z]+(?:[-\'][a-zA-Z]+)*\b'
    words = re.findall(word_pattern, content)

    # 过滤和清理单词
    filtered_words = []
    for word in words:
        # 转换为小写
        word = word.lower()

        # 过滤掉太短的单词
        if len(word) < 2:
            continue

        # 过滤掉纯数字或包含数字的单词
        if re.search(r'\d', word):
            continue

        # 过滤掉常见的非单词内容
        if word in ['www', 'http', 'https', 'com', 'org', 'net', 'html', 'css', 'js']:
            continue

        filtered_words.append(word)

    # 去除重复但保持原有顺序
    seen = set()
    unique_words = []
    for word in filtered_words:
        if word not in seen:
            seen.add(word)
            unique_words.append(word)

    return unique_words


def extract_vocabulary_entries(content):
    """
    提取词汇条目中的英文单词
    支持多种常见的词汇书格式
    """
    vocabulary_words = []

    # 模式1: <p class="bodytext">word <span class="yinbiao">/pronunciation/</span> part_of_speech. definition</p>
    pattern1 = r'<p\s+class="bodytext"[^>]*>([a-zA-Z]+(?:[-\'][a-zA-Z]+)*)\s*<span\s+class="yinbiao"[^>]*>.*?</span>.*?</p>'
    matches1 = re.findall(pattern1, content, re.IGNORECASE | re.DOTALL)
    vocabulary_words.extend(matches1)

    # 模式2: <p class="bodytext"><span class="text-title1">搭配</span> phrase 中文释义</p>
    pattern2 = r'<p\s+class="bodytext"[^>]*><span\s+class="text-title1"[^>]*>[^<]*</span>\s*([a-zA-Z]+(?:\s+[a-zA-Z]+)*(?:\s*[-\'][a-zA-Z]+)*)\s+[\u4e00-\u9fff].*?</p>'
    matches2 = re.findall(pattern2, content, re.IGNORECASE | re.DOTALL)
    vocabulary_words.extend(matches2)

    return vocabulary_words


def clean_html_content(content):
    """
    为备用方案清理HTML/XHTML标签和特殊字符
    """
    # 移除XML声明和DOCTYPE
    content = re.sub(r'<\?xml[^>]*\?>', '', content)
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content)

    # 移除CSS样式和JavaScript
    content = re.sub(r'<style[^>]*>.*?</style>', '',
                     content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<script[^>]*>.*?</script>',
                     '', content, flags=re.DOTALL | re.IGNORECASE)

    # 移除HTML标签
    content = re.sub(r'<[^>]+>', ' ', content)

    # 移除HTML实体
    html_entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'",
        '&nbsp;': ' ', '&mdash;': '-', '&ndash;': '-', '&rsquo;': "'",
        '&lsquo;': "'", '&rdquo;': '"', '&ldquo;': '"', '&hellip;': '...'
    }

    for entity, replacement in html_entities.items():
        content = content.replace(entity, replacement)

    # 移除其他HTML实体
    content = re.sub(r'&[a-zA-Z0-9#]+;', ' ', content)

    # 移除多余的空白字符
    content = re.sub(r'\s+', ' ', content)

    return content.strip()


def extract_words_from_content(content):
    """
    从内容中提取单词，优先使用结构化提取，备用通用提取
    """
    # 首先尝试从词汇条目中提取
    vocabulary_words = extract_vocabulary_entries(content)

    if vocabulary_words:
        print(f"从词汇条目中提取到 {len(vocabulary_words)} 个原始单词")

        # 过滤和清理词汇条目中的单词
        filtered_words = []
        for word in vocabulary_words:
            word = word.strip()

            # 过滤掉太短的单词
            if len(word) < 2:
                continue

            # 过滤掉包含数字的单词
            if re.search(r'\d', word):
                continue

            # 过滤掉常见的非单词内容
            if word in ['www', 'http', 'https', 'com', 'org', 'net', 'html', 'css', 'js']:
                continue

            filtered_words.append(word)

        print(f"过滤后剩余 {len(filtered_words)} 个有效单词")

        # 去除重复但保持原有顺序
        seen = set()
        unique_words = []
        for word in filtered_words:
            if word not in seen:
                seen.add(word)
                unique_words.append(word)

        return unique_words
    else:
        print("未找到标准词汇条目格式，使用备用提取方法...")
        # 备用方案：使用原来的通用提取方法
        cleaned_content = clean_html_content(content)
        return extract_english_words(cleaned_content)


def save_words_to_file(words, output_file):
    """
    将单词保存到文件
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for word in words:
                f.write(word + '\n')
        print(f"成功保存 {len(words)} 个唯一单词到 {output_file}")
    except Exception as e:
        print(f"保存文件时出错: {e}")


def get_epub_metadata(epub_file_path):
    """
    获取EPUB元数据（可选功能）
    """
    try:
        with zipfile.ZipFile(epub_file_path, 'r') as epub_zip:
            # 查找OPF文件
            opf_files = [f for f in epub_zip.namelist() if f.endswith('.opf')]

            if opf_files:
                with epub_zip.open(opf_files[0]) as opf_file:
                    opf_content = opf_file.read().decode('utf-8', errors='ignore')

                    # 简单提取标题
                    title_match = re.search(
                        r'<dc:title[^>]*>(.*?)</dc:title>', opf_content, re.IGNORECASE)
                    if title_match:
                        return title_match.group(1).strip()
    except:
        pass

    return None


def parse_page_range(page_range_str):
    """
    解析页码范围字符串
    支持格式: "5", "5-10", "5-", "-10"
    """
    if not page_range_str:
        return None, None

    if '-' not in page_range_str:
        # 单个页码
        try:
            page = int(page_range_str)
            return page, page
        except ValueError:
            raise ValueError(f"无效的页码: {page_range_str}")

    # 页码范围
    parts = page_range_str.split('-', 1)
    start_str, end_str = parts[0].strip(), parts[1].strip()

    try:
        start_page = int(start_str) if start_str else None
        end_page = int(end_str) if end_str else None

        if start_page is not None and end_page is not None and start_page > end_page:
            raise ValueError("起始页码不能大于结束页码")

        return start_page, end_page
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"无效的页码范围: {page_range_str}")
        raise


def main():
    """
    主函数
    """
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(
        description='从EPUB文件中提取英文单词',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
页码范围格式说明:
  5        - 只提取第5个文件
  5-10     - 提取第5-10个文件
  5-       - 从第5个文件开始到结束
  -10      - 从开始到第10个文件
  
示例:
  python epub_word_extractor.py book.epub
  python epub_word_extractor.py book.epub --pages 5-10
  python epub_word_extractor.py book.epub -p 5- -o output.txt
        '''
    )

    parser.add_argument('epub_file', help='EPUB文件路径')
    parser.add_argument('-p', '--pages', type=str,
                        help='页码范围 (例如: 5-10, 5-, -10, 5)')
    parser.add_argument('-o', '--output', type=str, help='输出文件名')
    parser.add_argument('--list-files', action='store_true',
                        help='列出EPUB中的所有内容文件')

    args = parser.parse_args()

    epub_file = args.epub_file

    # 检查文件是否存在
    if not os.path.exists(epub_file):
        print(f"错误: 文件 '{epub_file}' 不存在")
        sys.exit(1)

    # 检查文件扩展名
    if not epub_file.lower().endswith('.epub'):
        print("警告: 文件扩展名不是.epub，但仍会尝试处理")

    # 如果只是列出文件，则执行列表功能
    if args.list_files:
        print(f"正在分析文件: {epub_file}")
        ordered_files = get_epub_spine(epub_file)
        if ordered_files:
            print(f"\n找到 {len(ordered_files)} 个内容文件:")
            for i, file_path in enumerate(ordered_files, 1):
                print(f"  {i:3d}. {os.path.basename(file_path)}")
        else:
            print("未找到内容文件")
        sys.exit(0)

    # 解析页码范围
    start_page, end_page = None, None
    if args.pages:
        try:
            start_page, end_page = parse_page_range(args.pages)
            if start_page == end_page and start_page is not None:
                print(f"将提取第 {start_page} 个文件")
            elif start_page is not None and end_page is not None:
                print(f"将提取第 {start_page} 到第 {end_page} 个文件")
            elif start_page is not None:
                print(f"将从第 {start_page} 个文件开始提取到结束")
            elif end_page is not None:
                print(f"将从开始提取到第 {end_page} 个文件")
        except ValueError as e:
            print(f"错误: {e}")
            sys.exit(1)

    # 生成输出文件名
    if args.output:
        output_file = args.output
    else:
        base_name = Path(epub_file).stem
        if args.pages:
            page_suffix = args.pages.replace('-', '_')
            output_file = f"{base_name}_words_p{page_suffix}.txt"
        else:
            output_file = f"{base_name}_words.txt"

    print(f"开始处理文件: {epub_file}")

    # 获取EPUB元数据
    metadata = get_epub_metadata(epub_file)
    if metadata:
        print(f"书籍标题: {metadata}")

    # 提取EPUB内容
    print("正在提取EPUB文件内容...")
    content = extract_epub_content_by_range(epub_file, start_page, end_page)

    if not content:
        print("错误: 无法提取文件内容")
        sys.exit(1)

    print(f"提取到的内容长度: {len(content)} 字符")

    # 提取英文单词
    print("正在提取英文单词...")
    words = extract_words_from_content(content)

    if not words:
        print("警告: 未找到任何英文单词")
        sys.exit(1)

    # 显示一些统计信息
    print(f"找到 {len(words)} 个唯一单词")
    if len(words) > 10:
        print("前10个单词预览:")
        for i, word in enumerate(words[:10]):
            print(f"  {i+1}. {word}")

    # 保存到文件
    print("正在保存单词到文件...")
    save_words_to_file(words, output_file)

    print("\n处理完成!")
    print(f"输出文件: {output_file}")
    print(f"单词总数: {len(words)}")


if __name__ == "__main__":
    main()
