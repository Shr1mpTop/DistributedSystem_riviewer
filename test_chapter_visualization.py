#!/usr/bin/env python3
"""
章节分布测试脚本 - 专门测试章节占比可视化
"""

import sys
import json
import pandas as pd
from pathlib import Path

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent))
from src.data_processor import DataProcessor
from src.visualizer import ExamVisualizer

def test_chapter_distribution():
    """测试章节分布功能"""
    print("📚 测试章节分布分析")
    print("=" * 50)
    
    try:
        # 初始化组件
        processor = DataProcessor()
        visualizer = ExamVisualizer()
        print("✅ 组件初始化成功")
        
        # 加载数据
        test_file = "test_result_1.json"
        if Path(test_file).exists():
            print(f"📁 从测试文件加载数据: {test_file}")
            with open(test_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            questions = test_data.get('questions', [])
        else:
            questions = processor.load_parsed_questions()
            if not questions:
                print("❌ 没有找到题目数据")
                return
        
        print(f"✅ 加载了 {len(questions)} 道题目")
        
        # 处理数据
        df = processor.process_questions_to_dataframe(questions)
        print(f"✅ 数据处理完成，DataFrame形状: {df.shape}")
        
        # 检查refer字段的数据
        print(f"\n📊 Refer字段数据检查:")
        print(f"列名: {list(df.columns)}")
        if 'refer' in df.columns:
            print(f"Refer字段样本数据:")
            for i, refer in enumerate(df['refer'].head()):
                print(f"  {i+1}. {refer}")
        else:
            print("❌ 没有找到refer字段")
            return
        
        # 章节统计
        chapter_counts = df['refer'].value_counts()
        print(f"\n📈 章节分布统计:")
        for chapter, count in chapter_counts.items():
            percentage = count / len(df) * 100
            print(f"  {chapter}: {count}题 ({percentage:.1f}%)")
        
        # 生成章节分布图
        print(f"\n🎨 生成章节分布可视化...")
        try:
            result_path = visualizer.plot_chapter_distribution(df)
            print(f"✅ 章节分布图生成成功: {result_path}")
        except Exception as e:
            print(f"❌ 章节分布图生成失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 生成章节重要性分析图
        print(f"\n🎯 生成章节重要性分析...")
        try:
            result_path = visualizer.plot_chapter_importance_analysis(df)
            if result_path:
                print(f"✅ 章节重要性分析图生成成功: {result_path}")
            else:
                print("⚠️ 章节重要性分析图生成为空")
        except Exception as e:
            print(f"❌ 章节重要性分析图生成失败: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    test_chapter_distribution()

if __name__ == "__main__":
    main()