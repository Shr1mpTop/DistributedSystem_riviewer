#!/usr/bin/env python3
"""
单个PDF测试脚本 - 测试新的英文Prompt和无answer字段的PDF解析功能
为了百万年薪，必须确保完美工作！🎯
"""

import asyncio
import sys
from pathlib import Path
import json

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent))
from src.pdf_parser import PDFParser

async def test_single_pdf(pdf_path: str):
    """测试单个PDF文件的解析"""
    print(f"🔍 测试PDF文件: {pdf_path}")
    print("=" * 50)
    
    try:
        # 初始化解析器
        parser = PDFParser()
        print("✅ PDF解析器初始化成功")
        
        # 解析PDF
        result = await parser.parse_single_pdf(pdf_path)
        
        # 显示结果
        print(f"\n📊 解析结果:")
        print(f"提取题目数量: {len(result.get('questions', []))}")
        
        if result.get('questions'):
            print("\n📝 题目预览:")
            for i, question in enumerate(result['questions'][:3]):  # 只显示前3道题
                print(f"\n题目 {i+1}:")
                print(f"  ID: {question.get('id', 'N/A')}")
                print(f"  标题: {question.get('title', 'N/A')[:100]}...")
                print(f"  类型: {question.get('type', 'N/A')}")
                print(f"  章节: {question.get('refer', 'N/A')}")
                print(f"  知识点: {question.get('knowledge_points', [])}")
                print(f"  来源: {question.get('source', 'N/A')}")
            
            if len(result['questions']) > 3:
                print(f"\n... 还有 {len(result['questions']) - 3} 道题目")
        else:
            print("⚠️ 未提取到任何题目")
        
        # 保存测试结果
        test_output = f"test_result_{Path(pdf_path).stem}.json"
        with open(test_output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 测试结果已保存到: {test_output}")
        
        # 验证新格式
        if result.get('questions'):
            sample_question = result['questions'][0]
            print(f"\n🔍 格式验证:")
            print(f"  ✅ ID字段: {'id' in sample_question}")
            print(f"  ✅ 标题字段: {'title' in sample_question}")
            print(f"  ✅ 类型字段: {'type' in sample_question}")
            print(f"  ✅ 章节字段: {'refer' in sample_question}")
            print(f"  ✅ 知识点字段: {'knowledge_points' in sample_question}")
            print(f"  ✅ 来源字段: {'source' in sample_question}")
            print(f"  ❌ 答案字段(已移除): {'answer' not in sample_question}")
            
            # 验证知识点是否为数组格式
            kp = sample_question.get('knowledge_points', [])
            print(f"  ✅ 知识点为数组: {isinstance(kp, list)}")
            if isinstance(kp, list) and kp:
                print(f"     知识点示例: {kp[:3]}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("使用方法: python test_single_pdf.py <pdf_path>")
        print("示例: python test_single_pdf.py 1.pdf")
        return
    
    pdf_path = sys.argv[1]
    
    # 检查文件是否存在
    if not Path(pdf_path).exists():
        print(f"❌ 文件不存在: {pdf_path}")
        return
    
    await test_single_pdf(pdf_path)

if __name__ == "__main__":
    asyncio.run(main())