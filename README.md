# 生物信息学文献调研自动化工具

这是一个强大的生物信息学文献调研自动化工具，可以从多个学术数据源检索相关文献，并提供智能的关键词优化功能。

## 功能特点

- **多数据源支持**
  - PubMed
  - bioRxiv（预印本）
  - Google Scholar

- **智能关键词优化**
  - 自动生成相关的学术同义词
  - 支持领域特定的缩写和术语
  - 可通过参数禁用优化功能

- **高级功能**
  - 并行搜索多个数据源
  - bioRxiv 搜索的超时保护（3分钟）
  - 自动去重（基于标题）
  - Excel 格式结果输出
  - 实时保存已检索文献

## 安装步骤

1. 克隆仓库：
```bash
git clone [repository_url]
cd [repository_name]
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
创建 `.env` 文件并添加以下内容：
```
EMAIL=your_email@example.com
DEEPSEEK_API_KEY=your_api_key_here
```

## 使用方法

### 基本用法

```bash
python literature_pipeline.py -q "your search query"
```

### 完整参数说明

```bash
python literature_pipeline.py [-h] --query QUERY 
                            [--sources {pubmed,biorxiv,scholar} [{pubmed,biorxiv,scholar} ...]]
                            [--pubmed-count PUBMED_COUNT]
                            [--biorxiv-count BIORXIV_COUNT]
                            [--scholar-count SCHOLAR_COUNT]
                            [--email EMAIL]
                            [--no-optimize]
```

参数说明：
- `-q, --query`: 搜索关键词（必需）
- `-s, --sources`: 选择要搜索的数据源（默认：全部）
- `--pubmed-count`: PubMed检索文献数量（默认：20）
- `--biorxiv-count`: bioRxiv检索文献数量（默认：20）
- `--scholar-count`: Google Scholar检索文献数量（默认：20）
- `-e, --email`: 用于PubMed API的邮箱地址
- `--no-optimize`: 禁用关键词优化功能

### 使用示例

1. 基本搜索：
```bash
python literature_pipeline.py -q "Antimicrobial peptides"
```

2. 指定数据源：
```bash
python literature_pipeline.py -q "CRISPR" -s pubmed biorxiv
```

3. 自定义检索数量：
```bash
python literature_pipeline.py -q "Gene therapy" --pubmed-count 50 --biorxiv-count 30
```

4. 禁用关键词优化：
```bash
python literature_pipeline.py -q "Cancer immunotherapy" --no-optimize
```

## 输出说明

- 检索结果将保存在 `literature_results` 目录下
- 文件名格式：`literature_results_YYYYMMDD_HHMMSS.xlsx`
- Excel文件包含以下列：
  - source: 数据来源
  - title: 文章标题
  - authors: 作者列表
  - abstract: 摘要
  - url: 文章链接
  - id: 文章ID
  - published_date: 发布日期（仅bioRxiv）
  - category: 分类（仅bioRxiv）

## 注意事项

1. 确保提供有效的邮箱地址（用于PubMed API）
2. bioRxiv搜索设有3分钟超时限制
3. 为避免被封禁，Google Scholar搜索有延时机制
4. 关键词优化功能需要有效的DeepSeek API密钥

## 错误处理

- 如果搜索过程中出现错误，程序会继续处理其他数据源
- 对于超时的bioRxiv搜索，会保存已检索到的结果
- 所有错误和警告信息都会在控制台显示

## 依赖说明

主要依赖包：
- pandas
- biopython
- requests
- beautifulsoup4
- scholarly
- python-dotenv
- tqdm

详细的依赖列表请参见 `requirements.txt`。

## 贡献

欢迎提交Issue和Pull Request来帮助改进这个工具。

## 开发计划

未来可能添加的功能：
1. 支持更多的数据源
2. 添加高级搜索选项
3. 支持更多的输出格式
4. 添加文献分析功能
5. 支持批量检索 