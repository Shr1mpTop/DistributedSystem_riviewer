import json
import asyncio
import os
from typing import List, Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuestionExtender:
    def __init__(self, curriculum_data: Dict[str, Any]):
        """初始化问题扩展器"""
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("请在.env文件中设置GOOGLE_API_KEY")

        # 配置Google AI客户端
        self.client = genai.Client(api_key=self.api_key)
        self.curriculum_data = curriculum_data

    def create_extension_prompt(self, question: Dict[str, Any]) -> str:
        """创建用于扩展问题的提示"""
        curriculum_text = json.dumps(self.curriculum_data, ensure_ascii=False, indent=2)

        prompt = f"""You are an expert in distributed systems exam question analysis. Your task is to split compound questions into individual sub-questions.

Curriculum Information:
{curriculum_text}

Original Question Information:
ID: {question['id']}
Type: {question['type']}
Reference Chapter: {question['refer']}
Knowledge Points: {json.dumps(question['knowledge_points'], ensure_ascii=False)}
Source: {question['source']}
Question Content:
{question['title']}

Task Requirements:
1. Analyze the question content. If it contains multiple sub-questions (such as (a), (b), (c), etc.), split each sub-question into separate items.
2. If the question has only one part, do not split it and return the original question.
3. Each split sub-question must have:
   - A new ID (add letters to the original ID, such as Q001a, Q001b)
   - Keep the original type, refer, knowledge_points, source
   - Rewrite the title to contain only the content of that specific sub-question
   - Ensure the title format is clear and remove unnecessary markers

Return the split questions in JSON format as a list. Format example:
[
    {{
        "id": "Q001a",
        "title": "Complete content of sub-question (a)...",
        "type": "Original Type",
        "refer": "Original Reference Chapter",
        "knowledge_points": ["Original Knowledge Points"],
        "source": "Original Source"
    }},
    {{
        "id": "Q001b",
        "title": "Complete content of sub-question (b)...",
        "type": "Original Type",
        "refer": "Original Reference Chapter",
        "knowledge_points": ["Original Knowledge Points"],
        "source": "Original Source"
    }}
]

If no splitting is needed, return a single-element list containing the original question."""

        return prompt

    async def extend_single_question(self, question: Dict[str, Any], semaphore: asyncio.Semaphore) -> List[Dict[str, Any]]:
        """扩展单个问题"""
        async with semaphore:
            # 添加请求间隔以避免速率限制
            await asyncio.sleep(1)  # 1秒间隔
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    prompt = self.create_extension_prompt(question)

                    response = await asyncio.to_thread(
                        self.client.models.generate_content,
                        model="gemini-2.5-flash",
                        contents=[prompt]
                    )

                    response_text = response.text.strip()

                    # 尝试解析JSON响应
                    try:
                        # 移除可能的markdown代码块标记
                        if response_text.startswith('```json'):
                            response_text = response_text[7:]
                        if response_text.endswith('```'):
                            response_text = response_text[:-3]

                        extended_questions = json.loads(response_text.strip())

                        # 验证返回的数据结构
                        if not isinstance(extended_questions, list):
                            logger.warning(f"AI返回的不是列表格式: {question['id']}")
                            return [question]

                        for q in extended_questions:
                            if not all(key in q for key in ['id', 'title', 'type', 'refer', 'knowledge_points', 'source']):
                                logger.warning(f"AI返回的数据缺少必要字段: {question['id']}")
                                return [question]

                        logger.info(f"成功扩展题目 {question['id']} -> {len(extended_questions)} 个子问题")
                        return extended_questions

                    except json.JSONDecodeError as e:
                        logger.error(f"解析AI响应失败 {question['id']}: {e}")
                        logger.error(f"响应内容: {response_text}")
                        return [question]

                except Exception as e:
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 5  # 递增等待时间
                            logger.warning(f"题目 {question['id']} 遇到速率限制，等待 {wait_time} 秒后重试 ({attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"题目 {question['id']} 多次遇到速率限制，放弃处理")
                            return [question]
                    else:
                        logger.error(f"处理题目 {question['id']} 时出错: {e}")
                        if attempt < max_retries - 1:
                            logger.info(f"等待 2 秒后重试 ({attempt + 1}/{max_retries})")
                            await asyncio.sleep(2)
                            continue
                        return [question]

            # 所有重试都失败
            logger.error(f"题目 {question['id']} 处理失败，已达到最大重试次数")
            return [question]

    async def extend_questions(self, questions: List[Dict[str, Any]], concurrency: int = 1) -> List[Dict[str, Any]]:
        """并发扩展所有问题"""
        semaphore = asyncio.Semaphore(concurrency)
        tasks = [self.extend_single_question(question, semaphore) for question in questions]

        logger.info(f"开始并发处理 {len(questions)} 个题目，并发数: {concurrency}")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        extended_questions = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"任务 {i} 出现异常: {result}")
                # 返回原始问题
                extended_questions.append(questions[i])
            else:
                extended_questions.extend(result)

        logger.info(f"扩展完成，共生成 {len(extended_questions)} 个题目")
        return extended_questions

def load_curriculum(file_path: str) -> Dict[str, Any]:
    """加载课程大纲"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_parsed_questions(file_path: str) -> List[Dict[str, Any]]:
    """加载解析后的题目"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['questions']

def save_extended_questions(questions: List[Dict[str, Any]], output_path: str):
    """保存扩展后的题目"""
    output_data = {
        "questions": questions,
        "metadata": {
            "total_questions": len(questions),
            "generated_at": "2025-01-25",
            "description": "Extended questions with sub-questions split out"
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"扩展后的题目已保存到 {output_path}")

async def main():
    """主函数"""
    # 配置路径
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    curriculum_path = os.path.join(base_dir, 'data', 'curriculum.json')
    parsed_questions_path = os.path.join(base_dir, 'output', 'parsed_questions.json')
    output_path = os.path.join(base_dir, 'output', 'extended_questions.json')

    # 获取API密钥
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("请设置 GOOGLE_API_KEY 环境变量")

    # 加载数据
    logger.info("加载课程大纲和解析后的题目...")
    curriculum_data = load_curriculum(curriculum_path)
    questions = load_parsed_questions(parsed_questions_path)

    logger.info(f"加载了 {len(questions)} 个题目")

    # 创建扩展器
    extender = QuestionExtender(curriculum_data)

    # 扩展题目
    extended_questions = await extender.extend_questions(questions, concurrency=2)

    # 保存结果
    save_extended_questions(extended_questions, output_path)

if __name__ == "__main__":
    asyncio.run(main())