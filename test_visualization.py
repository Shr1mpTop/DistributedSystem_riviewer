#!/usr/bin/env python3
"""
可视化测试脚本 - 测试统计图表和数据分析功能
为了百万年薪，展示完美的数据可视化！📊
"""

import sys
import json
from pathlib import Path

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent))
from src.data_processor import DataProcessor
from src.visualizer import ExamVisualizer

def test_visualization():
    """测试可视化功能"""
    print("📊 测试可视化功能")
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
        
        # 生成统计信息
        stats = processor.generate_summary_statistics(df)
        print(f"✅ 统计信息生成完成")
        
        # 测试基础统计图表
        print(f"\n📈 生成基础统计图表...")
        
        # 1. 题型分布
        try:
            visualizer.plot_question_type_distribution(df)
            print("✅ 题型分布图生成成功")
        except Exception as e:
            print(f"❌ 题型分布图生成失败: {e}")
        
        # 2. 章节分布分析
        try:
            visualizer.plot_chapter_distribution(df)
            print("✅ 章节分布分析图生成成功")
        except Exception as e:
            print(f"❌ 章节分布分析图生成失败: {e}")
        
        # 3. 章节重要性分析
        try:
            visualizer.plot_chapter_importance_analysis(df)
            print("✅ 章节重要性分析图生成成功")
        except Exception as e:
            print(f"❌ 章节重要性分析图生成失败: {e}")
        
        # 4. 知识点分析（先检查数据格式）
        try:
            # 检查knowledge_points数据格式
            sample_kp = df['knowledge_points'].iloc[0] if not df.empty else None
            print(f"知识点数据样本: {sample_kp} (类型: {type(sample_kp)})")
            
            visualizer.plot_knowledge_points_analysis(df)
            print("✅ 知识点分析图生成成功")
        except Exception as e:
            print(f"❌ 知识点分析图生成失败: {e}")
        
        # 5. 交互式仪表板
        try:
            visualizer.create_interactive_dashboard(df)
            print("✅ 交互式仪表板生成成功")
        except Exception as e:
            print(f"❌ 交互式仪表板生成失败: {e}")
        
        # 检查生成的文件
        print(f"\n📁 检查生成的可视化文件...")
        viz_path = Path("output/visualizations")
        if viz_path.exists():
            files = list(viz_path.glob("*.png")) + list(viz_path.glob("*.html"))
            print(f"✅ 生成了 {len(files)} 个可视化文件:")
            for file in sorted(files):
                size = file.stat().st_size
                print(f"  📊 {file.name} ({size} bytes)")
        else:
            print("❌ 可视化目录不存在")
        
        # 显示统计摘要
        print(f"\n📈 数据分析摘要:")
        print(f"  题目总数: {stats['total_questions']}")
        print(f"  题型分布: {stats['question_types']}")
        print(f"  平均题目长度: {stats['avg_title_length']:.1f} 字符")
        print(f"  知识点覆盖率: {stats['knowledge_points_coverage']:.2%}")
        
        # 章节分布分析
        chapter_stats = df['refer'].value_counts()
        print(f"\n📚 章节分布分析:")
        for chapter, count in chapter_stats.head().items():
            percentage = count / len(df) * 100
            print(f"  {chapter}: {count}题 ({percentage:.1f}%)")
        
        print(f"\n🎯 可视化测试完成！")
        print(f"请查看 output/visualizations/ 目录中的图表文件")
        
    except Exception as e:
        print(f"❌ 可视化测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    test_visualization()

if __name__ == "__main__":
    main()