"""
数据处理模块 - 处理解析的JSON数据并导出为CSV
作者: 分布式系统考试指南项目组
功能: 将解析的题目JSON数据转换为CSV格式，便于后续分析
"""

import json
import csv
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any
import re

class DataProcessor:
    def __init__(self):
        """初始化数据处理器"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def load_parsed_questions(self, json_path: str = "output/parsed_questions.json") -> List[Dict[str, Any]]:
        """加载解析的题目JSON数据"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            questions = data.get('questions', [])
            self.logger.info(f"成功加载 {len(questions)} 道题目")
            return questions
            
        except FileNotFoundError:
            self.logger.error(f"文件不存在: {json_path}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            return []
    
    def clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not isinstance(text, str):
            return str(text)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除特殊字符但保留基本标点
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,;:!?()[\]{}""''""]+', '', text)
        
        return text
    
    def normalize_question_type(self, question_type: str) -> str:
        """标准化题型名称"""
        if not isinstance(question_type, str):
            return "未知题型"
        
        question_type = question_type.lower().strip()
        
        # 题型映射字典
        type_mapping = {
            # 选择题
            'choice': '选择题',
            'multiple choice': '选择题',
            'single choice': '选择题',
            'mcq': '选择题',
            '选择': '选择题',
            
            # 填空题
            'fill': '填空题',
            'fill in': '填空题',
            'fill-in': '填空题',
            'blank': '填空题',
            '填空': '填空题',
            
            # 简答题
            'short answer': '简答题',
            'brief answer': '简答题',
            '简答': '简答题',
            
            # 论述题
            'essay': '论述题',
            'discussion': '论述题',
            'long answer': '论述题',
            '论述': '论述题',
            '论证': '论述题',
            
            # 计算题
            'calculation': '计算题',
            'compute': '计算题',
            '计算': '计算题',
            
            # 编程题
            'programming': '编程题',
            'coding': '编程题',
            'code': '编程题',
            '编程': '编程题',
            '代码': '编程题',
            
            # 判断题
            'true/false': '判断题',
            'true false': '判断题',
            'boolean': '判断题',
            '判断': '判断题',
            '对错': '判断题'
        }
        
        # 查找匹配的题型
        for key, value in type_mapping.items():
            if key in question_type:
                return value
        
        return "其他题型"
    
    def extract_knowledge_points(self, refer: str, title: str) -> List[str]:
        """从题目内容中提取知识点"""
        knowledge_points = []
        
        # 从refer字段提取
        if isinstance(refer, str) and refer != "未提供":
            knowledge_points.append(refer)
        
        # 从题目标题中提取关键词
        if isinstance(title, str):
            # 分布式系统相关关键词
            keywords = [
                'RMI', 'Remote Method Invocation',
                'DHT', 'Distributed Hash Table',
                'P2P', 'Peer-to-Peer',
                'NFS', 'Network File System',
                'DNS', 'Domain Name System',
                'Clock', 'Synchronization',
                'Consistency', 'Replication',
                'Fault Tolerance', 'Availability',
                'Load Balancing', 'Scalability',
                'Marshalling', 'Serialization',
                'TCP', 'UDP', 'HTTP',
                'Client-Server', 'Architecture'
            ]
            
            title_lower = title.lower()
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    knowledge_points.append(keyword)
        
        return list(set(knowledge_points))  # 去重
    
    def process_questions_to_dataframe(self, questions: List[Dict[str, Any]]) -> pd.DataFrame:
        """将题目数据转换为DataFrame"""
        processed_data = []
        
        for question in questions:
            # 提取基本信息
            question_id = question.get('id', '')
            title = self.clean_text(question.get('title', ''))
            answer = self.clean_text(question.get('answer', '未提供'))
            refer = question.get('refer', '未提供')
            source = question.get('source', '未知')
            
            # 标准化题型
            original_type = question.get('type', '未知题型')
            normalized_type = self.normalize_question_type(original_type)
            
            # 提取知识点
            knowledge_points = self.extract_knowledge_points(refer, title)
            knowledge_points_str = '; '.join(knowledge_points) if knowledge_points else '未识别'
            
            # 计算题目长度（用于复杂度分析）
            title_length = len(title)
            answer_length = len(answer) if answer != '未提供' else 0
            
            processed_data.append({
                'id': question_id,
                'title': title,
                'type': normalized_type,
                'original_type': original_type,
                'answer': answer,
                'refer': refer,
                'knowledge_points': knowledge_points_str,
                'source': source,
                'title_length': title_length,
                'answer_length': answer_length,
                'has_answer': '是' if answer != '未提供' else '否'
            })
        
        df = pd.DataFrame(processed_data)
        self.logger.info(f"成功处理 {len(df)} 道题目数据")
        return df
    
    def export_to_csv(self, df: pd.DataFrame, output_path: str = "output/questions.csv"):
        """导出数据到CSV文件"""
        try:
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 导出核心字段到CSV
            core_columns = ['id', 'title', 'type', 'answer']
            core_df = df[core_columns]
            core_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            # 导出完整数据到另一个CSV
            full_output_path = output_path.replace('.csv', '_full.csv')
            df.to_csv(full_output_path, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"核心数据已导出到: {output_path}")
            self.logger.info(f"完整数据已导出到: {full_output_path}")
            
            return output_path, full_output_path
            
        except Exception as e:
            self.logger.error(f"CSV导出失败: {e}")
            return None, None
    
    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成数据统计摘要"""
        stats = {
            'total_questions': len(df),
            'question_types': df['type'].value_counts().to_dict(),
            'sources': df['source'].value_counts().to_dict(),
            'has_answer_ratio': (df['has_answer'] == '是').sum() / len(df),
            'avg_title_length': df['title_length'].mean(),
            'avg_answer_length': df[df['answer_length'] > 0]['answer_length'].mean()
        }
        
        return stats
    
    def save_statistics(self, stats: Dict[str, Any], output_path: str = "output/statistics.json"):
        """保存统计信息"""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"统计信息已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"统计信息保存失败: {e}")
            return None

def main():
    """主函数 - 演示数据处理功能"""
    processor = DataProcessor()
    
    # 加载解析的题目数据
    questions = processor.load_parsed_questions()
    
    if not questions:
        print("没有找到题目数据，请先运行PDF解析模块")
        return
    
    # 处理数据
    df = processor.process_questions_to_dataframe(questions)
    
    # 导出CSV
    csv_path, full_csv_path = processor.export_to_csv(df)
    
    # 生成统计信息
    stats = processor.generate_summary_statistics(df)
    stats_path = processor.save_statistics(stats)
    
    # 打印摘要
    print("\n=== 数据处理完成 ===")
    print(f"总题目数: {stats['total_questions']}")
    print(f"题型分布: {stats['question_types']}")
    print(f"有答案题目比例: {stats['has_answer_ratio']:.2%}")

if __name__ == "__main__":
    main()