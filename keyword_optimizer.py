import os
from typing import List, Dict
import requests
from dotenv import load_dotenv

class KeywordOptimizer:
    def __init__(self):
        """
        初始化关键词优化器
        """
        load_dotenv()
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("请在.env文件中设置DEEPSEEK_API_KEY")
            
        self.api_endpoint = "https://api.deepseek.com/v3/chat/completions"
        
    def optimize_keywords(self, query: str) -> Dict[str, List[str]]:
        """
        使用DeepSeek优化搜索关键词
        :param query: 原始搜索关键词
        :return: 优化后的关键词字典，包含不同类型的关键词列表
        """
        prompt = f"""
        作为一个生物信息学专家，请帮我优化以下搜索关键词，用于学术文献检索：
        原始关键词: {query}
        
        请提供以下几个方面的优化：
        1. 同义词和相关术语
        2. 更专业的学术表达
        3. 常见的缩写形式
        4. 相关的研究方法或技术
        5. 建议的布尔搜索组合
        
        请以JSON格式返回结果，包含以下字段：
        - synonyms: 同义词列表
        - academic_terms: 学术术语列表
        - abbreviations: 缩写列表
        - methods: 相关方法/技术列表
        - boolean_combinations: 布尔搜索组合列表
        """
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            
            # 解析返回的JSON结果
            result = response.json()
            optimized_keywords = result['choices'][0]['message']['content']
            
            # 处理返回的结果
            return self._process_response(optimized_keywords)
            
        except Exception as e:
            print(f"优化关键词时出错: {str(e)}")
            return self._get_default_optimization(query)
            
    def _process_response(self, response_text: str) -> Dict[str, List[str]]:
        """
        处理API返回的结果
        :param response_text: API返回的文本
        :return: 处理后的关键词字典
        """
        try:
            # 这里需要解析返回的JSON文本
            # 实际实现时可能需要更复杂的处理
            import json
            return json.loads(response_text)
        except:
            return self._get_default_optimization(response_text)
            
    def _get_default_optimization(self, query: str) -> Dict[str, List[str]]:
        """
        当API调用失败时返回默认的优化结果
        :param query: 原始查询词
        :return: 默认的优化结果
        """
        return {
            "synonyms": [query],
            "academic_terms": [query],
            "abbreviations": [],
            "methods": [],
            "boolean_combinations": [f"({query})"]
        }
        
    def generate_search_variations(self, query: str) -> List[str]:
        """
        生成多个搜索变体
        :param query: 原始搜索关键词
        :return: 搜索变体列表
        """
        optimized = self.optimize_keywords(query)
        variations = []
        
        # 添加原始查询
        variations.append(query)
        
        # 添加同义词搜索
        variations.extend(optimized["synonyms"])
        
        # 添加学术术语
        variations.extend(optimized["academic_terms"])
        
        # 添加缩写形式
        variations.extend(optimized["abbreviations"])
        
        # 添加布尔组合
        variations.extend(optimized["boolean_combinations"])
        
        # 去重并返回
        return list(set(variations))

def main():
    # 测试代码
    optimizer = KeywordOptimizer()
    query = "Antimicrobial peptides"
    print(f"原始关键词: {query}")
    print("\n优化结果:")
    optimized = optimizer.optimize_keywords(query)
    for category, terms in optimized.items():
        print(f"\n{category}:")
        for term in terms:
            print(f"- {term}")
            
if __name__ == "__main__":
    main() 