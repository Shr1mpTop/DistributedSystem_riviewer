#!/usr/bin/env python3
"""
CSV生成测试脚本 - 测试数据处理和CSV导出功能
为了百万年薪，确保数据处理完美！🎯
"""

import sys
import json
from pathlib import Path

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent))
from src.data_processor import DataProcessor

def test_csv_generation():
    """测试CSV生成功能"""
    print("🔍 测试CSV生成功能")
    print("=" * 50)
    
    try:
        # 初始化数据处理器
        processor = DataProcessor()
        print("✅ 数据处理器初始化成功")
        
        # 首先尝试从test_result_1.json加载数据
        test_file = "test_result_1.json"
        if Path(test_file).exists():
            print(f"📁 发现测试文件: {test_file}")
            with open(test_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            questions = test_data.get('questions', [])
            print(f"✅ 从测试文件加载了 {len(questions)} 道题目")
        else:
            # 回退到默认路径
            questions = processor.load_parsed_questions()
            if not questions:
                print("❌ 没有找到题目数据，请先运行PDF解析")
                print("提示：运行 python test_single_pdf.py 1.pdf 生成测试数据")
                return

        # 分析数据格式
        print(f"\n📊 数据分析:")
        print(f"题目总数: {len(questions)}")
        
        if questions:
            sample_question = questions[0]
            print(f"\n📝 样本题目结构:")
            for key, value in sample_question.items():
                print(f"  {key}: {type(value).__name__}")
                if key == 'knowledge_points' and isinstance(value, list):
                    print(f"    内容: {value}")
        
        # 处理数据转换为DataFrame
        print(f"\n🔄 处理数据...")
        df = processor.process_questions_to_dataframe(questions)
        print(f"✅ 数据处理完成，DataFrame形状: {df.shape}")
        
        # 显示DataFrame信息
        print(f"\n📈 DataFrame列信息:")
        for col in df.columns:
            print(f"  {col}: {df[col].dtype}")
        
        # 导出CSV
        print(f"\n💾 导出CSV文件...")
        csv_path, full_csv_path = processor.export_to_csv(df)
        
        if csv_path and full_csv_path:
            print(f"✅ CSV导出成功!")
            print(f"  核心数据: {csv_path}")
            print(f"  完整数据: {full_csv_path}")
            
            # 显示文件大小
            core_size = Path(csv_path).stat().st_size
            full_size = Path(full_csv_path).stat().st_size
            print(f"  核心文件大小: {core_size} bytes")
            print(f"  完整文件大小: {full_size} bytes")
        else:
            print("❌ CSV导出失败")
            return
        
        # 生成统计信息
        print(f"\n📊 生成统计信息...")
        stats = processor.generate_summary_statistics(df)
        stats_path = processor.save_statistics(stats)
        
        if stats_path:
            print(f"✅ 统计信息保存成功: {stats_path}")
        
        # 显示统计摘要
        print(f"\n📈 统计摘要:")
        print(f"  总题目数: {stats['total_questions']}")
        print(f"  题型分布: {stats['question_types']}")
        print(f"  平均题目长度: {stats['avg_title_length']:.1f} 字符")
        print(f"  知识点覆盖率: {stats['knowledge_points_coverage']:.2%}")
        
        # 预览CSV内容
        print(f"\n👀 CSV内容预览:")
        print("核心CSV前5行:")
        import pandas as pd
        preview_df = pd.read_csv(csv_path, nrows=5)
        for i, row in preview_df.iterrows():
            print(f"  {i+1}. ID: {row['id']}, 类型: {row['type']}")
            print(f"     题目: {row['title'][:80]}...")
            print(f"     章节: {row['refer']}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    test_csv_generation()

if __name__ == "__main__":
    main()