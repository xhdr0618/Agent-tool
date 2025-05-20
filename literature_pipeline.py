import os
from datetime import datetime
import pandas as pd
from Bio import Entrez
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
from scholarly import scholarly
import time
from dotenv import load_dotenv
import signal
from contextlib import contextmanager
import threading
from queue import Queue
import argparse
from keyword_optimizer import KeywordOptimizer

class TimeoutException(Exception):
    pass

@contextmanager
def timeout(seconds):
    """
    超时控制装饰器
    :param seconds: 超时时间（秒）
    """
    def timeout_handler(signum, frame):
        raise TimeoutException("操作超时")

    # 保存原有的信号处理器
    original_handler = signal.signal(signal.SIGALRM, timeout_handler)
    # 设置超时时间
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # 恢复原有的信号处理器
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)

class LiteraturePipeline:
    def __init__(self, email):
        """
        初始化文献调研管道
        :param email: 用于PubMed API的邮箱地址
        """
        Entrez.email = email
        self.results_dir = "literature_results"
        os.makedirs(self.results_dir, exist_ok=True)
        self.keyword_optimizer = None  # 初始化为None，在需要时才创建实例
        
    def optimize_query(self, query: str) -> dict:
        """
        使用关键词优化器优化搜索关键词
        :param query: 原始查询词
        :return: 优化后的查询词字典
        """
        if self.keyword_optimizer is None:
            try:
                self.keyword_optimizer = KeywordOptimizer()
            except ValueError as e:
                print(f"警告：无法初始化关键词优化器 - {str(e)}")
                return {"synonyms": [query], "academic_terms": [], "abbreviations": [], "methods": [], "boolean_combinations": []}
                
        try:
            variations = self.keyword_optimizer.optimize_keywords(query)
            if not isinstance(variations, dict):
                print(f"警告：关键词优化器返回了非字典格式的结果")
                return {"synonyms": [query], "academic_terms": [], "abbreviations": [], "methods": [], "boolean_combinations": []}
                
            print(f"\n关键词优化结果：")
            for category, terms in variations.items():
                print(f"\n{category}:")
                for term in terms:
                    print(f"- {term}")
            return variations
        except Exception as e:
            print(f"关键词优化失败: {str(e)}")
            return {"synonyms": [query], "academic_terms": [], "abbreviations": [], "methods": [], "boolean_combinations": []}

    def search_pubmed(self, query, max_results=20):
        """
        搜索PubMed数据库
        :param query: 搜索关键词
        :param max_results: 最大结果数量
        :return: 文章信息列表
        """
        print(f"\n正在搜索PubMed: {query}")
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        
        articles = []
        for id in tqdm(record["IdList"], desc="获取PubMed文章"):
            try:
                handle = Entrez.efetch(db="pubmed", id=id, rettype="medline", retmode="text")
                article = handle.read()
                handle.close()
                
                # 解析文章信息
                title = self._extract_field(article, "TI")
                authors = self._extract_field(article, "AU")
                abstract = self._extract_field(article, "AB")
                
                articles.append({
                    "source": "PubMed",
                    "id": id,
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{id}"
                })
                time.sleep(0.5)  # 避免请求过快
            except Exception as e:
                print(f"处理文章 {id} 时出错: {str(e)}")
                
        return articles
    
    def search_biorxiv(self, query, max_results=20, callback=None):
        """
        搜索bioRxiv预印本服务器
        :param query: 搜索关键词
        :param max_results: 最大结果数量
        :param callback: 回调函数，用于实时处理检索到的文章
        :return: 文章信息列表
        """
        print(f"\n正在搜索bioRxiv: {query}")
        articles = []
        
        try:
            # 清理查询词
            query = query.strip()
            if not query:
                print("搜索词不能为空")
                return articles
            
            # 使用bioRxiv的标准API端点
            base_url = "https://api.biorxiv.org/details/biorxiv"
            
            # 获取最近一年的文章
            from_date = "2024-05-01"
            to_date = "2025-05-01"
            
            try:
                # 首先获取总文章数
                url = f"{base_url}/{from_date}/{to_date}/0/1"
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
                # 确保获取到的total是整数
                try:
                    total_count = int(data.get("messages", [{}])[0].get("total", "0"))
                    total_results = min(max_results, total_count)
                except (ValueError, TypeError, IndexError):
                    print("无法获取总文章数，使用默认值")
                    total_results = max_results
                
                print(f"找到 {total_results} 篇潜在相关文章")
                
                # 使用tqdm显示总体进度
                with tqdm(total=total_results, desc="获取bioRxiv文章") as pbar:
                    current_page = 0
                    total_fetched = 0
                    
                    while total_fetched < total_results:
                        try:
                            url = f"{base_url}/{from_date}/{to_date}/{current_page}/100"
                            response = requests.get(url)
                            response.raise_for_status()
                            data = response.json()
                            
                            if not isinstance(data, dict) or "collection" not in data or not data["collection"]:
                                print("没有更多文章")
                                break
                            
                            for paper in data["collection"]:
                                if total_fetched >= total_results:
                                    break
                                    
                                title = str(paper.get("title", "")).lower()
                                abstract = str(paper.get("abstract", "")).lower()
                                query_lower = query.lower()
                                
                                if query_lower in title or query_lower in abstract:
                                    try:
                                        # 处理作者信息
                                        authors = paper.get("authors", "")
                                        if isinstance(authors, str):
                                            authors = [auth.strip() for auth in authors.split(";")]
                                        elif not authors:
                                            authors = []
                                        
                                        # 确保所有字段都是字符串类型
                                        article = {
                                            "source": "bioRxiv",
                                            "id": str(paper.get("doi", "")),
                                            "title": str(paper.get("title", "")),
                                            "authors": authors,
                                            "abstract": str(paper.get("abstract", "")),
                                            "url": f"https://www.biorxiv.org/content/{paper.get('doi')}v1" if paper.get('doi') else "",
                                            "published_date": str(paper.get("date", "")),
                                            "category": str(paper.get("category", ""))
                                        }
                                        
                                        articles.append(article)
                                        # 调用回调函数处理新检索到的文章
                                        if callback:
                                            callback(article)
                                            
                                        total_fetched += 1
                                        pbar.update(1)
                                        
                                    except Exception as e:
                                        print(f"处理文章数据时出错: {str(e)}")
                                        continue
                            
                            current_page += 100
                            time.sleep(1)
                            
                        except requests.exceptions.RequestException as e:
                            print(f"请求错误: {str(e)}")
                            if hasattr(e, 'response') and e.response is not None:
                                print(f"错误详情: {e.response.text}")
                            break
                        except Exception as e:
                            print(f"获取页面 {current_page} 时出错: {str(e)}")
                            break
                            
            except requests.exceptions.RequestException as e:
                print(f"初始请求错误: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"错误详情: {e.response.text}")
            except Exception as e:
                print(f"初始化搜索时出错: {str(e)}")
                
        except Exception as e:
            print(f"搜索bioRxiv时出错: {str(e)}")
            
        print(f"从bioRxiv获取到 {len(articles)} 篇文章")
        return articles
    
    def search_google_scholar(self, query, max_results=20):
        """
        搜索Google Scholar
        :param query: 搜索关键词
        :param max_results: 最大结果数量
        :return: 文章信息列表
        """
        print(f"\n正在搜索Google Scholar: {query}")
        articles = []
        search_query = scholarly.search_pubs(query)
        
        try:
            with tqdm(total=max_results, desc="获取Google Scholar文章") as pbar:
                for i in range(max_results):
                    try:
                        pub = next(search_query)
                        articles.append({
                            "source": "Google Scholar",
                            "id": pub.get("pub_url", ""),
                            "title": pub.get("bib", {}).get("title", ""),
                            "authors": pub.get("bib", {}).get("author", []),
                            "abstract": pub.get("bib", {}).get("abstract", ""),
                            "url": pub.get("pub_url", "")
                        })
                        pbar.update(1)
                        time.sleep(2)  # 避免被封IP
                    except StopIteration:
                        break
                    except Exception as e:
                        print(f"处理文章时出错: {str(e)}")
                        continue
                        
        except Exception as e:
            print(f"搜索Google Scholar时出错: {str(e)}")
            
        return articles
    
    def search_with_timeout(self, search_func, *args, timeout_seconds=180, **kwargs):
        """
        带超时控制的搜索函数
        :param search_func: 要执行的搜索函数
        :param timeout_seconds: 超时时间（秒）
        :return: 搜索结果
        """
        # 用于存储当前检索到的文章
        current_articles = []
        result_queue = Queue()
        
        def worker():
            try:
                # 如果是bioRxiv搜索函数，添加回调函数
                if search_func == self.search_biorxiv:
                    def article_callback(article):
                        current_articles.append(article)
                    kwargs['callback'] = article_callback
                    
                result = search_func(*args, **kwargs)
                result_queue.put(("success", result))
            except Exception as e:
                result_queue.put(("error", str(e)))
        
        thread = threading.Thread(target=worker)
        thread.daemon = True
        start_time = time.time()
        thread.start()
        
        # 等待指定时间
        thread.join(timeout_seconds)
        
        if thread.is_alive():
            elapsed_time = time.time() - start_time
            print(f"\n搜索已运行 {elapsed_time:.1f} 秒，超过设定的 {timeout_seconds} 秒限制")
            if current_articles:
                print(f"已成功检索到 {len(current_articles)} 篇文献，将保存这些结果")
                return current_articles
            else:
                print("尚未检索到任何文献")
                return []
            
        if not result_queue.empty():
            status, result = result_queue.get()
            if status == "success":
                return result
            else:
                print(f"搜索出错: {result}")
                if current_articles:
                    print(f"但已成功检索到 {len(current_articles)} 篇文献，将保存这些结果")
                    return current_articles
                return []
                
        return current_articles if current_articles else []

    def run_pipeline(self, query, include_sources=None, optimize_keywords=True):
        """
        运行完整的文献调研管道
        :param query: 搜索关键词
        :param include_sources: 要包含的数据源列表 ["pubmed", "biorxiv", "scholar"]
        :param optimize_keywords: 是否使用关键词优化
        :return: 保存的文件路径
        """
        if include_sources is None:
            include_sources = ["pubmed", "biorxiv", "scholar"]
            
        all_articles = []
        
        # 获取优化后的查询词列表
        if optimize_keywords:
            try:
                optimized = self.optimize_query(query)
                # 从优化结果中提取同义词
                queries = []
                # 添加原始查询
                queries.append(query)
                # 添加同义词
                queries.extend(optimized.get("synonyms", []))
                
                # 去重并过滤空字符串
                queries = list(set(filter(None, queries)))
                
                print("\n使用以下查询词进行搜索：")
                for q in queries:
                    print(f"- {q}")
                print()
            except Exception as e:
                print(f"关键词优化处理出错: {str(e)}")
                queries = [query]
        else:
            queries = [query]
        
        # 对每个优化后的查询词进行搜索
        for current_query in queries:
            print(f"\n使用查询词：{current_query}")
            
            if "pubmed" in include_sources:
                articles = self.search_pubmed(current_query)
                all_articles.extend(articles)
                print(f"从PubMed获取到 {len(articles)} 篇文献")
                
            if "biorxiv" in include_sources:
                print("\n正在搜索bioRxiv（设置3分钟超时）...")
                biorxiv_results = self.search_with_timeout(
                    self.search_biorxiv,
                    current_query,
                    timeout_seconds=180
                )
                all_articles.extend(biorxiv_results)
                
            if "scholar" in include_sources:
                articles = self.search_google_scholar(current_query)
                all_articles.extend(articles)
                print(f"从Google Scholar获取到 {len(articles)} 篇文献")
        
        # 去重（基于标题）
        unique_articles = []
        seen_titles = set()
        for article in all_articles:
            title = article['title'].lower().strip()
            if title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        
        # 转换为DataFrame并保存
        df = pd.DataFrame(unique_articles)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.results_dir, f"literature_results_{timestamp}.xlsx")
        
        # 重新组织列的顺序
        columns = ['source', 'title', 'authors', 'abstract', 'url', 'id']
        if 'published_date' in df.columns:
            columns.append('published_date')
        if 'category' in df.columns:
            columns.append('category')
        
        df = df[columns]
        df.to_excel(output_file, index=False)
        
        print(f"\n检索完成！共找到 {len(df)} 篇独特文献")
        print(f"结果已保存至: {output_file}")
        
        # 显示每个来源的文章数量
        if len(df) > 0:
            source_counts = df['source'].value_counts()
            print("\n各来源文章数量：")
            for source, count in source_counts.items():
                print(f"{source}: {count}篇")
        
        return output_file
    
    def _extract_field(self, text, field):
        """
        从MEDLINE格式文本中提取特定字段
        """
        lines = text.split("\n")
        field_content = []
        current_field = None
        
        for line in lines:
            if line.startswith(field + "  -"):
                current_field = field
                content = line[6:].strip()
                field_content.append(content)
            elif line.startswith("      ") and current_field == field:
                field_content.append(line.strip())
            else:
                current_field = None
                
        return " ".join(field_content)

if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='文献检索工具')
    
    # 添加参数
    parser.add_argument('--query', '-q', type=str, required=True,
                      help='搜索关键词，例如："Antimicrobial peptides"')
    
    parser.add_argument('--sources', '-s', type=str, nargs='+',
                      choices=['pubmed', 'biorxiv', 'scholar'],
                      default=['pubmed', 'biorxiv', 'scholar'],
                      help='选择要搜索的文献库，可多选。可选值: pubmed, biorxiv, scholar')
    
    parser.add_argument('--pubmed-count', type=int, default=20,
                      help='PubMed检索文献数量 (默认: 20)')
    
    parser.add_argument('--biorxiv-count', type=int, default=20,
                      help='bioRxiv检索文献数量 (默认: 20)')
    
    parser.add_argument('--scholar-count', type=int, default=20,
                      help='Google Scholar检索文献数量 (默认: 20)')
    
    parser.add_argument('--email', '-e', type=str,
                      help='用于PubMed API的邮箱地址。如果不提供，将从.env文件读取')
    
    parser.add_argument('--no-optimize', action='store_true',
                      help='禁用关键词优化功能')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 获取邮箱地址
    email = args.email
    if not email:
        load_dotenv()
        email = os.getenv("EMAIL")
        if not email:
            print("错误：未提供邮箱地址。请通过--email参数提供或在.env文件中设置EMAIL变量")
            exit(1)
    
    # 创建pipeline实例
    pipeline = LiteraturePipeline(email)
    
    # 保存原始方法的引用
    original_pubmed_search = pipeline.search_pubmed
    original_biorxiv_search = pipeline.search_biorxiv
    original_google_scholar_search = pipeline.search_google_scholar
    
    # 设置每个数据源的检索数量，正确处理callback参数
    pipeline.search_pubmed = lambda q, **kwargs: original_pubmed_search(q, max_results=args.pubmed_count)
    pipeline.search_biorxiv = lambda q, **kwargs: original_biorxiv_search(q, max_results=args.biorxiv_count, **kwargs)
    pipeline.search_google_scholar = lambda q, **kwargs: original_google_scholar_search(q, max_results=args.scholar_count)
    
    # 执行搜索
    print("\n搜索配置：")
    print(f"关键词: {args.query}")
    print(f"选择的数据源: {', '.join(args.sources)}")
    print(f"PubMed文献数量: {args.pubmed_count}")
    print(f"bioRxiv文献数量: {args.biorxiv_count}")
    print(f"Google Scholar文献数量: {args.scholar_count}")
    print(f"使用邮箱: {email}")
    print(f"关键词优化: {'禁用' if args.no_optimize else '启用'}")
    print("\n开始搜索...\n")
    
    # 运行检索
    results_file = pipeline.run_pipeline(
        query=args.query,
        include_sources=args.sources,
        optimize_keywords=not args.no_optimize
    ) 