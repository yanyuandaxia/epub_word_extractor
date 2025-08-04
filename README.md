### 1. **页码范围提取**
- 支持多种格式：`5`（单页）、`5-10`（范围）、`5-`（从第5页到结束）、`-10`（从开始到第10页）
- 基于EPUB的章节/文件顺序，而不是传统的页码概念

### 2. **EPUB结构分析**
- 自动解析EPUB的spine（阅读顺序）
- 按照标准EPUB结构提取内容文件

### 3. **文件列表功能**
- 使用`--list-files`参数可以查看EPUB中所有内容文件

## 使用方法：

### 基本用法：
```bash
# 提取整本书的单词
python epub_word_extractor.py book.epub

# 提取第5到第10个文件的单词
python epub_word_extractor.py book.epub --pages 5-10

# 从第5个文件开始到结束
python epub_word_extractor.py book.epub -p 5-

# 从开始到第10个文件
python epub_word_extractor.py book.epub -p -10

# 只提取第5个文件
python epub_word_extractor.py book.epub -p 5

# 指定输出文件名
python epub_word_extractor.py book.epub -p 5-10 -o chapter5_10_words.txt
```

### 查看文件结构：
```bash
# 列出EPUB中的所有内容文件
python epub_word_extractor.py book.epub --list-files
```

## 主要改进：

1. **智能文件排序**：根据EPUB的OPF文件中的spine顺序排列文件
2. **灵活的范围指定**：支持多种页码范围格式
3. **详细的进度信息**：显示正在处理的文件和进度
4. **命令行参数**：使用argparse提供更好的用户界面
5. **输出文件命名**：根据页码范围自动生成文件名

## 输出示例：
```
开始处理文件: vocabulary.epub
书籍标题: English Vocabulary Builder
找到 15 个内容文件
将提取第 5 到第 10 个文件
正在提取EPUB文件内容...
  处理文件 5/15: chapter05.xhtml
  处理文件 6/15: chapter06.xhtml
  ...
  处理文件 10/15: chapter10.xhtml
提取到的内容长度: 45230 字符
正在清理内容...
正在提取英文单词...
找到 1248 个唯一单词
前10个单词预览:
  1. abandon
  2. ability
  3. about
  ...
正在保存单词到文件...
成功保存 1248 个唯一单词到 vocabulary_words_p5_10.txt

处理完成!
输出文件: vocabulary_words_p5_10.txt
单词总数: 1248
```