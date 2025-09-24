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
        """Create extraction prompt in English for better Gemini performance"""
        curriculum_str = json.dumps(self.curriculum, ensure_ascii=False, indent=2)

        prompt = f"""
## 🎯 CRITICAL INSTRUCTION - MUST FOLLOW EXACTLY 🎯

You are a top-tier exam question extraction expert. Your task is to extract exam questions from this PDF document and output them in the specified JSON format strictly.

**⚠️ IMPORTANT: Your response must be pure JSON format without any other text explanation!**

### 📚 Course Curriculum Reference (for knowledge point matching):
{curriculum_str}

### 🔒 MANDATORY OUTPUT FORMAT - MUST STRICTLY FOLLOW:
{{
  "questions": [
    {{
      "id": "Q001",
      "title": "Complete question description including all sub-questions (a), (b), (c) if they belong to the same main question",
      "type": "Multiple Choice|Fill in Blank|Short Answer|Essay|Calculation|True/False|Programming",
      "refer": "Corresponding course chapter name",
      "knowledge_points": ["specific knowledge point 1", "specific knowledge point 2", "specific knowledge point 3"]
    }}
  ]
}}

### 📋 STRICT EXECUTION RULES:
1. **MUST output valid JSON** - No non-JSON content is accepted
2. **id format**: Q001, Q002, Q003... incrementally
3. **title**: Complete question description for each individual sub-question
4. **type**: Must be one of: Multiple Choice, Fill in Blank, Short Answer, Essay, Calculation, True/False, Programming
5. **refer**: Match to curriculum chapters based on question content, format like "Chapter 1 Characterization of Distributed Systems & System Models"
6. **knowledge_points**: Must be array format, containing specific knowledge points related to this question

### 🎯 QUESTION IDENTIFICATION PATTERNS - CRITICAL FOR SUB-QUESTION EXTRACTION:
- **SUB-QUESTION SEPARATION**: If you see questions with (a), (b), (c) sub-questions, EACH sub-question should be extracted as a SEPARATE question entry
- **INDIVIDUAL EXTRACTION**: Extract (a), (b), (c), (d), etc. as separate, independent questions
- **CONTEXT INCLUSION**: Include necessary context from the main question in each sub-question title
- **COMPLETE SUB-QUESTION**: Each sub-question should be self-contained with full context
- **NO DUPLICATES**: If you encounter the same question multiple times, extract it ONLY ONCE
- **UNIQUE IDENTIFICATION**: Each question should have unique content - do not repeat identical questions

### 🎯 KNOWLEDGE POINT ANALYSIS RULES:
- Carefully analyze question content and find matching knowledge points from curriculum content arrays
- knowledge_points must be array format: ["knowledge point 1", "knowledge point 2", "knowledge point 3"]
- Prioritize selecting 1-3 most relevant specific knowledge points
- If no matching knowledge points found, use ["Uncategorized"]

### 🎯 QUESTION IDENTIFICATION PATTERNS:
- Look for numbering: 1., 2., (1), (2), Q1, Question 1, etc.
- Look for sub-question markers: (a), (b), (c), (i), (ii), (iii), etc.
- Identify question marks, choice options, fill-in blanks
- Look for "Answer", "Solution", etc. keywords but DO NOT include answers in output
- **CRITICAL**: Extract EACH sub-question (a), (b), (c) as a SEPARATE question entry

### 🎯 SUB-QUESTION EXTRACTION EXAMPLES:
- **Input**: "Three processes p1, p2 and p3... (a) What is... (b) Calculate... (c) Explain..."
- **Output**: THREE separate questions:
  - Question 1: "Three processes p1, p2 and p3... (a) What is..."
  - Question 2: "Three processes p1, p2 and p3... (b) Calculate..."
  - Question 3: "Three processes p1, p2 and p3... (c) Explain..."

### ⚡ OUTPUT REQUIREMENTS:
- Output JSON directly, do not wrap in ```json``` code blocks
- Do not add any explanatory text
- Ensure JSON format is completely correct and parseable
- If no questions found, output: {{"questions": []}}

Please carefully analyze this PDF document and extract all exam questions WITH proper sub-question separation:"""
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
                    model="gemini-2.5-pro",  
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
                        # 确保所有必需字段存在（移除answer字段）
                        fixed_question = {
                            'id': question.get('id', f'Q{i+1:03d}'),
                            'title': str(question.get('title', '')).strip(),
                            'type': str(question.get('type', 'Unknown')).strip(),
                            'refer': str(question.get('refer', 'Uncategorized')).strip(),
                            'knowledge_points': question.get('knowledge_points', ['Uncategorized'])
                        }
                        
                        # 确保knowledge_points是列表格式
                        if not isinstance(fixed_question['knowledge_points'], list):
                            if isinstance(fixed_question['knowledge_points'], str):
                                fixed_question['knowledge_points'] = [fixed_question['knowledge_points']]
                            else:
                                fixed_question['knowledge_points'] = ['Uncategorized']
                        
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

        # 保存单个PDF的解析结果
        self.save_single_pdf_result(result, pdf_name)

        return result
    
    def save_single_pdf_result(self, result: Dict[str, Any], pdf_name: str):
        """保存单个PDF的解析结果"""
        try:
            # 确保输出目录存在
            output_dir = Path("output/pdf_results")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成输出文件名（移除.pdf扩展名）
            base_name = pdf_name.replace('.pdf', '')
            output_path = output_dir / f"{base_name}_result.json"
            
            # 保存结果
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"单个PDF结果已保存: {output_path}")
            
        except Exception as e:
            self.logger.error(f"保存单个PDF结果失败 {pdf_name}: {e}")
    
    async def parse_all_pdfs(self, pdf_directory: str = ".", concurrency: int = 2) -> List[Dict[str, Any]]:
        """并发解析所有PDF文件（控制并发数避免API速率限制）"""
        pdf_files = list(Path(pdf_directory).glob("*.pdf"))
        
        if not pdf_files:
            self.logger.warning("未找到PDF文件")
            return []
        
        self.logger.info(f"发现 {len(pdf_files)} 个PDF文件")
        self.logger.info(f"使用并发处理，并发数: {concurrency}")
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(concurrency)
        
        async def parse_with_semaphore(pdf_file: Path) -> Dict[str, Any]:
            """使用信号量控制的PDF解析函数"""
            async with semaphore:
                self.logger.info(f"开始处理: {pdf_file.name}")
                result = await self.parse_single_pdf(str(pdf_file))
                self.logger.info(f"完成处理: {pdf_file.name} ({len(result.get('questions', []))} 道题目)")
                return result
        
        # 创建所有解析任务
        tasks = [parse_with_semaphore(pdf_file) for pdf_file in pdf_files]
        
        # 使用进度条显示处理进度
        with tqdm(total=len(pdf_files), desc="解析PDF文件") as pbar:
            # 分批执行任务，避免一次性创建太多任务
            results = []
            batch_size = concurrency * 2  # 批次大小为并发数的2倍
            
            for i in range(0, len(tasks), batch_size):
                batch_tasks = tasks[i:i + batch_size]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # 处理结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        self.logger.error(f"PDF解析出现异常: {result}")
                        results.append({'questions': []})  # 添加空结果
                    else:
                        results.append(result)
                    
                    pbar.update(1)
                
                # 批次间添加短暂延迟，避免API过载
                if i + batch_size < len(tasks):
                    await asyncio.sleep(1)
        
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