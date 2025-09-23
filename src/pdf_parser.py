"""
PDF解析模块 - 使用Google AI提取考试题目
作者: 分布式系统考试指南项目组
功能: 解析PDF文件中的考试题目，输出标准化JSON格式
"""

import os
import json
import asyncio
import logging
import time
from typing import List, Dict, Any
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tqdm import tqdm

# 加载环境变量
load_dotenv()

class PDFParser:
    def __init__(self):
        """初始化PDF解析器"""
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("请在.env文件中设置GOOGLE_API_KEY")
        
        # 配置Google AI客户端
        self.client = genai.Client(api_key=self.api_key)
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 加载课程大纲用于知识点映射
        self.curriculum = self._load_curriculum()
        
        # API速率限制控制
        self.last_api_call = 0
        self.min_interval = 30  # 免费版限制：每分钟2次请求，安全起见30秒一次
    
    def _load_curriculum(self) -> Dict[str, Any]:
        """加载课程大纲JSON数据"""
        try:
            curriculum_path = Path('data/curriculum.json')
            with open(curriculum_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"无法加载课程大纲: {e}")
            return {}
    
    def wait_for_rate_limit(self):
        """控制API调用速率，避免超出限制"""
        current_time = time.time()
        elapsed = current_time - self.last_api_call
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            self.logger.info(f"等待 {wait_time:.1f} 秒以避免速率限制...")
            time.sleep(wait_time)
        self.last_api_call = time.time()
    
    def create_extraction_prompt(self) -> str:
        """创建用于题目提取的超级严格提示词 - 为了百万年薪！"""
        curriculum_str = json.dumps(self.curriculum, ensure_ascii=False, indent=2)
        
        prompt = f"""
## 🎯 CRITICAL INSTRUCTION - MUST FOLLOW EXACTLY 🎯

你是一个顶级的考试题目提取专家。你的任务是从这个PDF文档中提取考试题目，并且必须严格按照指定的JSON格式输出。

**⚠️ 重要：你的回复必须是纯JSON格式，不能包含任何其他文字说明！**

### 📚 课程大纲参考（用于匹配知识点）:
{curriculum_str}

### 🔒 强制输出格式 - 必须严格遵守：
{{
  "questions": [
    {{
      "id": "Q001",
      "title": "题目的完整描述，包括所有选项（如果是选择题）",
      "type": "选择题|填空题|简答题|论述题|计算题|判断题|编程题",
      "answer": "标准答案或未提供",
      "refer": "对应的课程章节名称"
    }}
  ]
}}

### 📋 严格执行规则：
1. **必须输出有效JSON** - 任何非JSON内容都不被接受
2. **id格式**: Q001, Q002, Q003... 依次递增
3. **title**: 包含题目完整内容，选择题要包含所有选项A、B、C、D
4. **type**: 只能是以下之一：选择题、填空题、简答题、论述题、计算题、判断题、编程题
5. **answer**: 如果PDF中有答案就写答案，没有就写"未提供"
6. **refer**: 根据题目内容匹配到课程大纲中的章节，格式如"第1章 分布式系统特征与系统模型"

### 🎯 题目识别模式：
- 寻找序号：1., 2., (1), (2), Q1, Question 1 等
- 识别问号、选择项、填空线
- 寻找"答案"、"解答"、"Answer"等关键词

### ⚡ 输出要求：
- 直接输出JSON，不要包装在```json```代码块中
- 不要添加任何解释文字
- 确保JSON格式完全正确，可被程序解析
- 如果没找到题目，输出：{{"questions": []}}

请仔细分析这个PDF文档并提取所有考试题目："""
        return prompt
    
    async def analyze_pdf_with_ai(self, pdf_path: str, pdf_name: str, max_retries: int = 3) -> Dict[str, Any]:
        """使用Google AI直接分析PDF文件并提取题目"""
        for attempt in range(max_retries):
            try:
                # 控制API调用速率
                self.wait_for_rate_limit()
                
                # 创建提示词
                prompt = self.create_extraction_prompt()
                
                self.logger.info(f"正在分析 {pdf_name}... (尝试 {attempt + 1}/{max_retries})")
                
                # 读取PDF文件为字节数据
                pdf_path_obj = Path(pdf_path)
                pdf_bytes = pdf_path_obj.read_bytes()
                
                # 使用新的Google AI API直接处理PDF
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model="gemini-2.5-flash",  # 使用flash版本，更快更便宜
                    contents=[
                        types.Part.from_bytes(
                            data=pdf_bytes,
                            mime_type='application/pdf',
                        ),
                        prompt
                    ]
                )
                
                # 📋 超级智能JSON解析 - 为了百万年薪！
                response_text = response.text.strip()
                self.logger.info(f"AI响应长度: {len(response_text)} 字符")
                
                # 🔍 多种方式尝试提取JSON
                json_candidates = []
                
                # 方式1: 寻找```json代码块
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    if json_end > json_start:
                        json_candidates.append(response_text[json_start:json_end].strip())
                
                # 方式2: 寻找第一个{到最后一个}
                if '{' in response_text and '}' in response_text:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    json_candidates.append(response_text[json_start:json_end])
                
                # 方式3: 如果没有找到，尝试整个响应
                json_candidates.append(response_text)
                
                # 🎯 尝试解析每个候选JSON
                result = None
                for i, candidate in enumerate(json_candidates):
                    try:
                        result = json.loads(candidate)
                        self.logger.info(f"JSON解析成功 (方式 {i+1})")
                        break
                    except json.JSONDecodeError:
                        continue
                
                if result is None:
                    raise json.JSONDecodeError("所有JSON解析方式都失败", response_text, 0)
                
                # ✅ 验证和修复结果格式
                if not isinstance(result, dict):
                    result = {'questions': []}
                elif 'questions' not in result:
                    result = {'questions': []}
                elif not isinstance(result['questions'], list):
                    result = {'questions': []}
                
                # 🔧 验证每个题目格式
                valid_questions = []
                for i, question in enumerate(result['questions']):
                    if isinstance(question, dict):
                        # 确保所有必需字段存在
                        fixed_question = {
                            'id': question.get('id', f'Q{i+1:03d}'),
                            'title': str(question.get('title', '')).strip(),
                            'type': str(question.get('type', '未知题型')).strip(),
                            'answer': str(question.get('answer', '未提供')).strip(),
                            'refer': str(question.get('refer', '未分类')).strip()
                        }
                        
                        # 只保留有效题目（至少有标题）
                        if fixed_question['title']:
                            valid_questions.append(fixed_question)
                
                result['questions'] = valid_questions
                
                self.logger.info(f"{pdf_name} 解析完成，提取到 {len(result['questions'])} 道题目")
                return result
                
            except json.JSONDecodeError as e:
                self.logger.error(f"{pdf_name} JSON解析失败 (尝试 {attempt + 1}): {e}")
                if 'response_text' in locals():
                    self.logger.error(f"AI响应内容: {response_text[:500]}...")
                if attempt == max_retries - 1:
                    return {'questions': []}
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    self.logger.warning(f"{pdf_name} 遇到速率限制 (尝试 {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        # 从错误消息中提取重试延迟
                        import re
                        retry_match = re.search(r'retry in (\d+(?:\.\d+)?)s', error_msg)
                        if retry_match:
                            retry_delay = float(retry_match.group(1)) + 1  # 添加额外1秒缓冲
                            self.logger.info(f"等待 {retry_delay:.1f} 秒后重试...")
                            await asyncio.sleep(retry_delay)
                        else:
                            await asyncio.sleep(60)  # 默认等待60秒
                        continue
                else:
                    self.logger.error(f"{pdf_name} AI分析失败 (尝试 {attempt + 1}): {e}")
                    if attempt == max_retries - 1:
                        return {'questions': []}
        
        return {'questions': []}
    
    async def parse_single_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """解析单个PDF文件"""
        pdf_name = Path(pdf_path).name
        self.logger.info(f"开始处理: {pdf_name}")
        
        # 检查PDF文件是否存在且大小合适
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            self.logger.error(f"PDF文件不存在: {pdf_path}")
            return {'questions': []}
        
        file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
        if file_size_mb > 20:
            self.logger.warning(f"{pdf_name} 文件过大 ({file_size_mb:.1f}MB)，可能会处理失败")
        
        # 使用AI直接分析PDF
        result = await self.analyze_pdf_with_ai(pdf_path, pdf_name)
        
        # 为每个题目添加源文件信息
        for question in result.get('questions', []):
            question['source'] = pdf_name
        
        return result
    
    async def parse_all_pdfs(self, pdf_directory: str = ".") -> List[Dict[str, Any]]:
        """串行解析所有PDF文件（避免API速率限制）"""
        pdf_files = list(Path(pdf_directory).glob("*.pdf"))
        
        if not pdf_files:
            self.logger.warning("未找到PDF文件")
            return []
        
        self.logger.info(f"发现 {len(pdf_files)} 个PDF文件")
        self.logger.info("使用串行处理以避免API速率限制...")
        
        results = []
        
        # 使用进度条显示处理进度
        with tqdm(total=len(pdf_files), desc="解析PDF文件") as pbar:
            for i, pdf_file in enumerate(pdf_files):
                self.logger.info(f"处理第 {i+1}/{len(pdf_files)} 个文件: {pdf_file.name}")
                
                # 在每个文件之间添加短暂延迟
                if i > 0:
                    await asyncio.sleep(2)  # 2秒延迟以避免速率限制
                
                result = await self.parse_single_pdf(str(pdf_file))
                results.append(result)
                pbar.update(1)
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_path: str = "output/parsed_questions.json"):
        """保存解析结果到JSON文件"""
        # 合并所有结果
        all_questions = []
        for result in results:
            all_questions.extend(result.get('questions', []))
        
        # 为题目重新编号
        for i, question in enumerate(all_questions, 1):
            question['id'] = f"Q{i:03d}"
        
        # 保存结果
        output_data = {
            'total_questions': len(all_questions),
            'questions': all_questions,
            'metadata': {
                'extracted_at': str(Path().resolve()),
                'pdf_count': len(results)
            }
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"解析结果已保存到: {output_path}")
        self.logger.info(f"总共提取到 {len(all_questions)} 道题目")
        
        return output_data

async def main():
    """主函数 - 演示PDF解析功能"""
    parser = PDFParser()
    
    # 解析所有PDF文件
    results = await parser.parse_all_pdfs()
    
    # 保存结果
    parser.save_results(results)

if __name__ == "__main__":
    asyncio.run(main())