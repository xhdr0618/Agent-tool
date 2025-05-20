import os
from typing import List, Dict
import requests
from dotenv import load_dotenv
import json

class KeywordOptimizer:
    def __init__(self):
        """
        初始化关键词优化器
        """
        load_dotenv()
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("请在.env文件中设置DEEPSEEK_API_KEY")
            
        self.api_endpoint = "https://api.deepseek.com/chat/completions"
        
    def optimize_keywords(self, query: str) -> Dict[str, List[str]]:
        """
        使用DeepSeek优化搜索关键词
        :param query: 原始搜索关键词
        :return: 优化后的关键词字典，主要包含同义词
        """
        prompt = f"""
        作为一个生物信息学专家，请为以下搜索关键词提供学术文献检索用的同义词。
        原始关键词: {query}
        
        请提供5-10个最相关的同义词或相近表达，要求：
        1. 必须是学术文献中常用的表达方式
        2. 应该包括该领域常用的缩写形式（如果有）
        3. 每个词都应该是独立的搜索词，不要包含布尔操作符
        4. 保持简洁，每个同义词不超过3-4个单词
        
        只需返回一个JSON对象，格式如下：
        {{
            "synonyms": [
                "term1",
                "term2",
                "term3"
            ]
        }}
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
            
            # 打印原始响应以便调试
            print("\nAPI响应内容：")
            print(optimized_keywords)
            
            # 处理返回的结果
            processed_result = self._process_response(optimized_keywords)
            
            # 打印处理后的结果以便调试
            print("\n处理后的结果：")
            print(processed_result)
            
            return processed_result
            
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
            # 清理响应文本
            json_str = response_text.strip()
            
            # 如果文本以```json开头，去掉这部分
            if "```json" in json_str:
                json_str = json_str.split("```json")[1]
            if "```" in json_str:
                json_str = json_str.split("```")[0]
                
            # 去掉可能的前后缀说明文字
            start_idx = json_str.find('{')
            end_idx = json_str.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = json_str[start_idx:end_idx]
            
            # 解析JSON
            result = json.loads(json_str)
            
            # 确保返回的是字典格式且包含synonyms字段
            if isinstance(result, dict) and "synonyms" in result:
                # 过滤掉空字符串和None值，并清理每个词
                synonyms = []
                for term in result["synonyms"]:
                    if term and isinstance(term, str):
                        cleaned_term = term.strip().strip('"').strip("'")
                        if cleaned_term:
                            synonyms.append(cleaned_term)
                            
                # 去重
                synonyms = list(set(synonyms))
                return {"synonyms": synonyms}
            else:
                print("API返回的格式不正确")
                return self._get_default_optimization(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {str(e)}")
            print(f"尝试解析的文本: {json_str}")
            return self._get_default_optimization(response_text)
        except Exception as e:
            print(f"处理API响应时出错: {str(e)}")
            return self._get_default_optimization(response_text)
            
    def _get_default_optimization(self, query: str) -> Dict[str, List[str]]:
        """
        当API调用失败时返回默认的优化结果
        :param query: 原始查询词
        :return: 默认的优化结果
        """
        return {"synonyms": [query]}
        
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