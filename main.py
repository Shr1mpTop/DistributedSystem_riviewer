"""
分布式系统考试指南 - 主控制程序
作者: 分布式系统考试指南项目组
功能: 协调所有模块，实现完整的工作流程

工作流程:
1. 加载课程大纲JSON数据
2. 并行解析PDF试卷，提取题目信息
3. 数据处理和CSV导出
4. 可视化分析和统计报告
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any

# 导入自定义模块
sys.path.append(str(Path(__file__).parent))
from src.pdf_parser import PDFParser
from src.data_processor import DataProcessor
from src.visualizer import ExamVisualizer

class DistributedSystemExamAnalyzer:
    def __init__(self):
        """初始化考试分析器"""
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('exam_analyzer.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个模块
        self.pdf_parser = None
        self.data_processor = DataProcessor()
        self.visualizer = ExamVisualizer()
        
        # 项目配置
        self.config = {
            'project_name': 'NTU分布式系统考试指南',
            'version': '1.0.0',
            'author': '分布式系统考试指南项目组',
            'created_at': datetime.now().isoformat()
        }
    
    def check_environment(self) -> bool:
        """检查运行环境"""
        self.logger.info("正在检查运行环境...")
        
        # 检查.env文件
        if not Path('.env').exists():
            self.logger.warning("未找到.env文件，请从.env.template复制并配置")
            return False
        
        # 检查必要目录
        required_dirs = ['data', 'output', 'src']
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                self.logger.error(f"缺少必要目录: {dir_name}")
                return False
        
        # 检查课程大纲文件
        if not Path('data/curriculum.json').exists():
            self.logger.error("未找到课程大纲文件: data/curriculum.json")
            return False
        
        # 检查PDF文件
        pdf_files = list(Path('.').glob('*.pdf'))
        if not pdf_files:
            self.logger.warning("未找到PDF文件，请将考试试卷PDF放置在项目根目录")
            return False
        
        self.logger.info(f"环境检查完成，发现 {len(pdf_files)} 个PDF文件")
        return True
    
    def initialize_pdf_parser(self) -> bool:
        """初始化PDF解析器"""
        try:
            self.pdf_parser = PDFParser()
            self.logger.info("PDF解析器初始化成功")
            return True
        except ValueError as e:
            self.logger.error(f"PDF解析器初始化失败: {e}")
            self.logger.error("请检查.env文件中的GOOGLE_API_KEY配置")
            return False
        except Exception as e:
            self.logger.error(f"PDF解析器初始化出现未知错误: {e}")
            return False
    
    async def run_pdf_analysis(self) -> bool:
        """运行PDF分析阶段"""
        self.logger.info("=== 开始PDF分析阶段 ===")
        
        try:
            # 解析所有PDF文件
            results = await self.pdf_parser.parse_all_pdfs()
            
            # 保存解析结果
            output_data = self.pdf_parser.save_results(results)
            
            if output_data['total_questions'] == 0:
                self.logger.warning("未提取到任何题目，请检查PDF文件内容")
                return False
            
            self.logger.info(f"PDF分析完成，提取到 {output_data['total_questions']} 道题目")
            return True
            
        except Exception as e:
            self.logger.error(f"PDF分析阶段失败: {e}")
            return False
    
    def run_data_processing(self) -> bool:
        """运行数据处理阶段"""
        self.logger.info("=== 开始数据处理阶段 ===")
        
        try:
            # 加载解析的题目数据
            questions = self.data_processor.load_parsed_questions()
            
            if not questions:
                self.logger.error("没有找到解析的题目数据")
                return False
            
            # 处理数据
            df = self.data_processor.process_questions_to_dataframe(questions)
            
            # 导出CSV
            csv_path, full_csv_path = self.data_processor.export_to_csv(df)
            
            if not csv_path:
                self.logger.error("CSV导出失败")
                return False
            
            # 生成统计信息
            stats = self.data_processor.generate_summary_statistics(df)
            stats_path = self.data_processor.save_statistics(stats)
            
            self.logger.info("数据处理阶段完成")
            return True
            
        except Exception as e:
            self.logger.error(f"数据处理阶段失败: {e}")
            return False
    
    def run_visualization(self) -> bool:
        """运行可视化分析阶段"""
        self.logger.info("=== 开始可视化分析阶段 ===")
        
        try:
            # 生成所有可视化
            results = self.visualizer.generate_all_visualizations()
            
            if not results:
                self.logger.error("可视化生成失败")
                return False
            
            self.logger.info("可视化分析阶段完成")
            return True
            
        except Exception as e:
            self.logger.error(f"可视化分析阶段失败: {e}")
            return False
    
    def generate_final_report(self) -> str:
        """生成最终分析报告"""
        self.logger.info("=== 生成最终报告 ===")
        
        try:
            # 加载各阶段的结果
            report_data = {
                'config': self.config,
                'analysis_date': datetime.now().isoformat(),
                'stages': {
                    'pdf_analysis': 'completed',
                    'data_processing': 'completed',
                    'visualization': 'completed'
                }
            }
            
            # 尝试加载统计信息
            try:
                with open('output/statistics.json', 'r', encoding='utf-8') as f:
                    report_data['statistics'] = json.load(f)
            except FileNotFoundError:
                self.logger.warning("未找到统计信息文件")
            
            # 尝试加载洞察报告
            try:
                with open('output/visualizations/exam_insights_report.json', 'r', encoding='utf-8') as f:
                    report_data['insights'] = json.load(f)
            except FileNotFoundError:
                self.logger.warning("未找到洞察报告文件")
            
            # 生成文件清单
            output_files = []
            output_dir = Path('output')
            if output_dir.exists():
                for file_path in output_dir.rglob('*'):
                    if file_path.is_file():
                        output_files.append(str(file_path.relative_to('.')))
            
            report_data['output_files'] = output_files
            
            # 保存最终报告
            report_path = 'output/final_analysis_report.json'
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"最终报告已生成: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"最终报告生成失败: {e}")
            return ""
    
    def print_summary(self):
        """打印执行摘要"""
        print("\n" + "="*60)
        print(f"🎓 {self.config['project_name']} - 分析完成")
        print("="*60)
        
        try:
            # 读取统计信息
            with open('output/statistics.json', 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            print(f"📊 总题目数量: {stats['total_questions']}")
            print(f"📝 题型分布: {stats['question_types']}")
            print(f"✅ 答案完整率: {stats['has_answer_ratio']:.2%}")
            
        except FileNotFoundError:
            print("📊 统计信息未找到")
        
        print("\n📁 输出文件:")
        output_files = [
            "output/questions.csv - 核心题目数据",
            "output/questions_full.csv - 完整题目数据", 
            "output/statistics.json - 统计信息",
            "output/visualizations/ - 可视化图表",
            "output/final_analysis_report.json - 最终报告"
        ]
        
        for file_desc in output_files:
            if Path(file_desc.split(' - ')[0]).exists():
                print(f"  ✅ {file_desc}")
            else:
                print(f"  ❌ {file_desc}")
        
        print("\n🎯 建议:")
        print("  1. 查看 output/visualizations/interactive_dashboard.html 获取交互式分析")
        print("  2. 参考 output/visualizations/exam_insights_report.json 了解学习重点")
        print("  3. 使用 output/questions.csv 进行进一步的数据分析")
        print("="*60)
    
    async def run_full_analysis(self):
        """运行完整的分析流程"""
        self.logger.info(f"🚀 启动 {self.config['project_name']}")
        
        # 1. 环境检查
        if not self.check_environment():
            self.logger.error("环境检查失败，程序退出")
            sys.exit(1)
        
        # 2. 初始化PDF解析器
        if not self.initialize_pdf_parser():
            self.logger.error("PDF解析器初始化失败，程序退出")
            sys.exit(1)
        
        # 3. PDF分析
        if not await self.run_pdf_analysis():
            self.logger.error("PDF分析失败，程序退出")
            sys.exit(1)
        
        # 4. 数据处理
        if not self.run_data_processing():
            self.logger.error("数据处理失败，程序退出")
            sys.exit(1)
        
        # 5. 可视化分析
        if not self.run_visualization():
            self.logger.error("可视化分析失败，程序退出")
            sys.exit(1)
        
        # 6. 生成最终报告
        final_report = self.generate_final_report()
        
        # 7. 打印摘要
        self.print_summary()
        
        self.logger.info("🎉 分析流程全部完成！")

async def main():
    """主函数"""
    analyzer = DistributedSystemExamAnalyzer()
    await analyzer.run_full_analysis()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序执行出现错误: {e}")
        sys.exit(1)