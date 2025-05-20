# 生物信息学文献调研自动化工具

这是一个用于自动化文献调研的Python工具，专门针对生物信息学领域。该工具可以从多个学术数据库获取文献信息，包括：

- PubMed
- bioRxiv
- Google Scholar

## 功能特点

- 多数据源整合搜索
- 自动提取文章标题、作者、摘要等信息
- 结果自动保存为Excel格式
- 内置请求限制，避免被封IP
- 支持自定义搜索源和检索数量
- 支持命令行参数控制
- bioRxiv搜索支持3分钟超时保护（保存已检索文献）

## 安装要求

1. Python 3.7+
2. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 配置环境

创建`.env`文件并添加您的邮箱地址（用于PubMed API）：
```
EMAIL=your.email@example.com
```

### 2. 命令行使用

基本使用：
```bash
python literature_pipeline.py -q "your search query"
```

完整参数说明：
```bash
python literature_pipeline.py \
    -q "Antimicrobial peptides" \          # 搜索关键词（必需）
    -s pubmed biorxiv scholar \            # 选择数据源
    --pubmed-count 50 \                    # PubMed文献数量
    --biorxiv-count 30 \                   # bioRxiv文献数量
    --scholar-count 20 \                   # Google Scholar文献数量
    -e your.email@example.com              # 邮箱地址（可选）
```

### 3. 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --query | -q | 搜索关键词（必需） | - |
| --sources | -s | 要搜索的数据库 | pubmed,biorxiv,scholar |
| --pubmed-count | - | PubMed检索数量 | 20 |
| --biorxiv-count | - | bioRxiv检索数量 | 20 |
| --scholar-count | - | Google Scholar检索数量 | 20 |
| --email | -e | PubMed API邮箱 | 从.env读取 |

### 4. 使用示例

1. **只搜索PubMed，检索50篇文献**：
```bash
python literature_pipeline.py -q "RNA" -s pubmed --pubmed-count 50
```

2. **搜索多个数据源，自定义数量**：
```bash
python literature_pipeline.py -q "CRISPR" -s pubmed biorxiv --pubmed-count 30 --biorxiv-count 20
```

3. **使用引号包含的短语**：
```bash
python literature_pipeline.py -q "single cell RNA sequencing"
```

## 输出结果

结果将保存在`literature_results`目录下，文件名格式为`literature_results_YYYYMMDD_HHMMSS.xlsx`，包含以下字段：

- source: 数据来源
- id: 文章ID/DOI
- title: 文章标题
- authors: 作者列表
- abstract: 文章摘要
- url: 文章链接
- published_date: 发布日期（仅部分来源支持）
- category: 文章分类（仅部分来源支持）

## 注意事项

1. **PubMed API使用**：
   - 需要提供有效的邮箱地址
   - 可以通过命令行参数或.env文件配置

2. **Google Scholar注意事项**：
   - 有请求频率限制
   - 建议适当控制检索数量
   - 每次请求间有2秒延迟

3. **bioRxiv搜索说明**：
   - 设置了3分钟超时保护
   - 超时时会保存已检索到的文献
   - 支持实时保存检索结果

4. **一般建议**：
   - 建议根据实际需求调整检索数量
   - 关键词越具体，结果越相关
   - 可以分多次检索，使用不同的关键词

## 错误处理

1. 如果遇到API错误：
   - 检查网络连接
   - 验证邮箱地址是否正确
   - 确认API访问限制

2. 如果结果为空：
   - 尝试使用更通用的关键词
   - 检查选择的数据源是否正确
   - 增加检索数量

## 贡献

欢迎提交Issue和Pull Request来帮助改进这个工具。

## 开发计划

未来可能添加的功能：
1. 支持更多的数据源
2. 添加高级搜索选项
3. 支持更多的输出格式
4. 添加文献分析功能
5. 支持批量检索 