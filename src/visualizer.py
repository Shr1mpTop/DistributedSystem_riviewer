"""
可视化分析模块 - 分析题型分布和知识点统计
作者: 分布式系统考试指南项目组
功能: 生成各种统计图表，分析考试趋势和重点
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import re
from collections import Counter

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ExamVisualizer:
    def __init__(self):
        """初始化可视化分析器"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 设置颜色主题
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'accent': '#F18F01',
            'success': '#C73E1D',
            'warning': '#FFC300',
            'info': '#4CAF50'
        }
        
        # 设置输出目录
        self.output_dir = Path('output/visualizations')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_data(self, csv_path: str = "output/questions_full.csv") -> pd.DataFrame:
        """加载处理后的题目数据"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            self.logger.info(f"成功加载 {len(df)} 条数据")
            return df
        except FileNotFoundError:
            self.logger.error(f"文件不存在: {csv_path}")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            return pd.DataFrame()
    
    def analyze_question_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析题型分布"""
        type_counts = df['type'].value_counts()
        type_percentages = df['type'].value_counts(normalize=True) * 100
        
        analysis = {
            'counts': type_counts.to_dict(),
            'percentages': type_percentages.to_dict(),
            'total_types': len(type_counts),
            'most_common': type_counts.index[0] if not type_counts.empty else None,
            'least_common': type_counts.index[-1] if not type_counts.empty else None
        }
        
        return analysis
    
    def analyze_knowledge_points(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析知识点分布"""
        # 提取所有知识点
        all_knowledge_points = []
        for kp_str in df['knowledge_points'].dropna():
            if kp_str != '未识别':
                points = [kp.strip() for kp in kp_str.split(';')]
                all_knowledge_points.extend(points)
        
        # 统计知识点频率
        kp_counter = Counter(all_knowledge_points)
        
        analysis = {
            'total_unique_points': len(kp_counter),
            'top_10_points': dict(kp_counter.most_common(10)),
            'total_mentions': sum(kp_counter.values()),
            'coverage_rate': len([kp for kp in df['knowledge_points'] if kp != '未识别']) / len(df)
        }
        
        return analysis
    
    def plot_question_type_distribution(self, df: pd.DataFrame) -> str:
        """绘制题型分布图"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 题型计数柱状图
        type_counts = df['type'].value_counts()
        bars1 = ax1.bar(range(len(type_counts)), type_counts.values, 
                       color=[self.colors['primary'], self.colors['secondary'], 
                             self.colors['accent'], self.colors['success']][:len(type_counts)])
        ax1.set_title('题型数量分布', fontsize=14, fontweight='bold')
        ax1.set_xlabel('题型')
        ax1.set_ylabel('题目数量')
        ax1.set_xticks(range(len(type_counts)))
        ax1.set_xticklabels(type_counts.index, rotation=45, ha='right')
        
        # 在柱状图上添加数值标签
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        # 题型比例饼图
        colors_pie = [self.colors['primary'], self.colors['secondary'], 
                     self.colors['accent'], self.colors['success'], 
                     self.colors['warning'], self.colors['info']]
        
        wedges, texts, autotexts = ax2.pie(type_counts.values, labels=type_counts.index, 
                                          autopct='%1.1f%%', startangle=90,
                                          colors=colors_pie[:len(type_counts)])
        ax2.set_title('题型比例分布', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # 保存图片
        output_path = self.output_dir / 'question_type_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"题型分布图已保存: {output_path}")
        return str(output_path)
    
    def plot_chapter_importance_analysis(self, df: pd.DataFrame) -> str:
        """绘制章节重要程度和题型分布分析图 - 为了百万年薪！"""
        # 分析refer字段，提取章节信息
        chapter_data = []
        
        for _, row in df.iterrows():
            refer = str(row.get('refer', ''))
            question_type = str(row.get('type', ''))
            
            # 从refer中提取章节号
            chapter_match = re.search(r'第(\d+)章', refer)
            if chapter_match:
                chapter_num = int(chapter_match.group(1))
                chapter_data.append({
                    'chapter': chapter_num,
                    'type': question_type,
                    'refer': refer
                })
        
        if not chapter_data:
            self.logger.warning("没有找到章节相关数据")
            return ""
        
        # 转换为DataFrame
        chapter_df = pd.DataFrame(chapter_data)
        
        # 统计每个章节的题目数量
        chapter_counts = chapter_df['chapter'].value_counts().sort_index()
        
        # 统计每个章节的题型分布
        chapter_type_matrix = pd.crosstab(chapter_df['chapter'], chapter_df['type'])
        
        # 创建子图
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 子图1: 章节重要程度条形图
        chapters = [f'第{i}章' for i in range(1, 8)]
        chapter_values = [chapter_counts.get(i, 0) for i in range(1, 8)]
        
        bars1 = ax1.bar(range(len(chapters)), chapter_values, 
                       color=[self.colors['primary'], self.colors['secondary'], 
                             self.colors['accent'], self.colors['success'],
                             self.colors['warning'], self.colors['info'], '#9C27B0'])
        ax1.set_title('📊 章节重要程度分析 (题目数量)', fontsize=16, fontweight='bold', pad=20)
        ax1.set_xlabel('课程章节', fontsize=12)
        ax1.set_ylabel('题目数量', fontsize=12)
        ax1.set_xticks(range(len(chapters)))
        ax1.set_xticklabels(chapters, rotation=45, ha='right')
        
        # 添加数值标签
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        # 子图2: 章节题型分布堆叠条形图
        chapter_type_matrix = chapter_type_matrix.reindex(range(1, 8), fill_value=0)
        chapter_type_matrix.plot(kind='bar', stacked=True, ax=ax2, 
                               color=[self.colors['primary'], self.colors['secondary'], 
                                     self.colors['accent'], self.colors['success'],
                                     self.colors['warning'], self.colors['info']])
        ax2.set_title('🎯 章节题型分布分析', fontsize=16, fontweight='bold', pad=20)
        ax2.set_xlabel('课程章节', fontsize=12)
        ax2.set_ylabel('题目数量', fontsize=12)
        ax2.legend(title='题型', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.set_xticklabels([f'第{i}章' for i in range(1, 8)], rotation=45, ha='right')
        
        # 子图3: 题型在各章节的分布热力图
        if not chapter_type_matrix.empty:
            sns.heatmap(chapter_type_matrix.T, annot=True, fmt='d', 
                       cmap='YlOrRd', ax=ax3, cbar_kws={'label': '题目数量'})
            ax3.set_title('🔥 题型-章节热力图分析', fontsize=16, fontweight='bold', pad=20)
            ax3.set_xlabel('课程章节', fontsize=12)
            ax3.set_ylabel('题型', fontsize=12)
            ax3.set_xticklabels([f'第{i}章' for i in range(1, 8)], rotation=45, ha='right')
        
        # 子图4: 章节覆盖率饼图
        total_questions = len(df)
        chapter_coverage = [(count / total_questions) * 100 for count in chapter_values]
        
        wedges, texts, autotexts = ax4.pie(chapter_coverage, 
                                          labels=[f'第{i}章\n({chapter_values[i-1]})' for i in range(1, 8)],
                                          autopct='%1.1f%%', startangle=90,
                                          colors=[self.colors['primary'], self.colors['secondary'], 
                                                 self.colors['accent'], self.colors['success'],
                                                 self.colors['warning'], self.colors['info'], '#9C27B0'])
        ax4.set_title('📈 章节覆盖率分析', fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # 保存图片
        output_path = self.output_dir / 'chapter_importance_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight', bbox_extra_artists=[])
        plt.close()
        
        self.logger.info(f"章节重要程度分析图已保存: {output_path}")
        return str(output_path)
    
    def plot_knowledge_points_analysis(self, df: pd.DataFrame) -> str:
        """绘制知识点分析图"""
        # 提取知识点数据
        all_knowledge_points = []
        for kp_str in df['knowledge_points'].dropna():
            if kp_str != '未识别':
                points = [kp.strip() for kp in kp_str.split(';')]
                all_knowledge_points.extend(points)
        
        if not all_knowledge_points:
            self.logger.warning("没有找到知识点数据")
            return ""
        
        kp_counter = Counter(all_knowledge_points)
        top_10_kp = dict(kp_counter.most_common(10))
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 知识点频率柱状图
        kp_names = list(top_10_kp.keys())
        kp_counts = list(top_10_kp.values())
        
        bars = ax1.barh(range(len(kp_names)), kp_counts, 
                       color=self.colors['secondary'])
        ax1.set_title('Top 10 最常考知识点', fontsize=14, fontweight='bold')
        ax1.set_xlabel('出现频次')
        ax1.set_yticks(range(len(kp_names)))
        ax1.set_yticklabels(kp_names)
        ax1.invert_yaxis()
        
        # 在柱状图上添加数值标签
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax1.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                    f'{int(width)}', ha='left', va='center')
        
        # 知识点覆盖率分析
        coverage_data = []
        for _, row in df.iterrows():
            kp_str = row['knowledge_points']
            if kp_str == '未识别' or pd.isna(kp_str):
                coverage_data.append('未识别')
            else:
                kp_count = len([kp.strip() for kp in kp_str.split(';')])
                if kp_count == 1:
                    coverage_data.append('单个知识点')
                elif kp_count <= 3:
                    coverage_data.append('2-3个知识点')
                else:
                    coverage_data.append('3+个知识点')
        
        coverage_counts = pd.Series(coverage_data).value_counts()
        
        wedges, texts, autotexts = ax2.pie(coverage_counts.values, 
                                          labels=coverage_counts.index,
                                          autopct='%1.1f%%', startangle=90,
                                          colors=[self.colors['primary'], 
                                                 self.colors['accent'],
                                                 self.colors['success'],
                                                 self.colors['warning']])
        ax2.set_title('题目知识点覆盖情况', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # 保存图片
        output_path = self.output_dir / 'knowledge_points_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"知识点分析图已保存: {output_path}")
        return str(output_path)
    
    def create_interactive_dashboard(self, df: pd.DataFrame) -> str:
        """创建交互式仪表板"""
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('题型分布', '来源分布', '答案完整性', '题目复杂度'),
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # 题型分布柱状图
        type_counts = df['type'].value_counts()
        fig.add_trace(
            go.Bar(x=type_counts.index, y=type_counts.values,
                   name="题型分布", marker_color=self.colors['primary']),
            row=1, col=1
        )
        
        # 来源分布饼图
        source_counts = df['source'].value_counts()
        fig.add_trace(
            go.Pie(labels=source_counts.index, values=source_counts.values,
                   name="来源分布"),
            row=1, col=2
        )
        
        # 答案完整性
        answer_status = df['has_answer'].value_counts()
        fig.add_trace(
            go.Bar(x=answer_status.index, y=answer_status.values,
                   name="答案完整性", marker_color=self.colors['secondary']),
            row=2, col=1
        )
        
        # 题目复杂度散点图
        fig.add_trace(
            go.Scatter(x=df['title_length'], y=df['answer_length'],
                      mode='markers', name="复杂度分析",
                      text=df['type'], hovertemplate='<b>%{text}</b><br>题目长度: %{x}<br>答案长度: %{y}',
                      marker=dict(color=df['title_length'], 
                                colorscale='Viridis', size=8)),
            row=2, col=2
        )
        
        # 更新布局
        fig.update_layout(
            title_text="分布式系统考试题目分析仪表板",
            showlegend=False,
            height=800
        )
        
        # 保存交互式图表
        output_path = self.output_dir / 'interactive_dashboard.html'
        fig.write_html(output_path)
        
        self.logger.info(f"交互式仪表板已保存: {output_path}")
        return str(output_path)
    
    def generate_exam_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成考试洞察报告"""
        insights = {
            'overview': {
                'total_questions': len(df),
                'total_sources': df['source'].nunique(),
                'question_types': df['type'].nunique(),
                'answer_coverage': (df['has_answer'] == '是').mean() * 100
            },
            'type_analysis': self.analyze_question_types(df),
            'knowledge_analysis': self.analyze_knowledge_points(df),
            'difficulty_analysis': {
                'avg_title_length': df['title_length'].mean(),
                'avg_answer_length': df[df['answer_length'] > 0]['answer_length'].mean(),
                'complex_questions': len(df[df['title_length'] > df['title_length'].quantile(0.75)])
            },
            'recommendations': self._generate_recommendations(df)
        }
        
        return insights
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """生成学习建议"""
        recommendations = []
        
        # 基于题型分布的建议
        type_counts = df['type'].value_counts()
        most_common_type = type_counts.index[0]
        recommendations.append(f"重点关注{most_common_type}，占比{type_counts.iloc[0]/len(df)*100:.1f}%")
        
        # 基于知识点的建议
        all_kp = []
        for kp_str in df['knowledge_points'].dropna():
            if kp_str != '未识别':
                all_kp.extend([kp.strip() for kp in kp_str.split(';')])
        
        if all_kp:
            kp_counter = Counter(all_kp)
            top_kp = kp_counter.most_common(3)
            recommendations.append(f"高频知识点：{', '.join([kp[0] for kp in top_kp])}")
        
        # 基于答案完整性的建议
        answer_rate = (df['has_answer'] == '是').mean()
        if answer_rate < 0.5:
            recommendations.append("建议补充更多标准答案，提高复习效果")
        
        return recommendations
    
    def save_insights_report(self, insights: Dict[str, Any], output_path: str = None) -> str:
        """保存洞察报告"""
        if output_path is None:
            output_path = self.output_dir / 'exam_insights_report.json'
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(insights, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"洞察报告已保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"报告保存失败: {e}")
            return ""
    
    def generate_all_visualizations(self, csv_path: str = "output/questions_full.csv") -> Dict[str, str]:
        """生成所有可视化图表"""
        # 加载数据
        df = self.load_data(csv_path)
        if df.empty:
            self.logger.error("无法加载数据，停止可视化生成")
            return {}
        
        # 生成各种图表
        results = {}
        
        try:
            # 题型分布图
            results['type_distribution'] = self.plot_question_type_distribution(df)
            
            # 章节重要程度分析图
            results['chapter_importance'] = self.plot_chapter_importance_analysis(df)
            
            # 知识点分析图
            results['knowledge_analysis'] = self.plot_knowledge_points_analysis(df)
            
            # 交互式仪表板
            results['interactive_dashboard'] = self.create_interactive_dashboard(df)
            
            # 生成洞察报告
            insights = self.generate_exam_insights(df)
            results['insights_report'] = self.save_insights_report(insights)
            
            self.logger.info("所有可视化图表生成完成")
            
        except Exception as e:
            self.logger.error(f"可视化生成过程中出现错误: {e}")
        
        return results

def main():
    """主函数 - 演示可视化功能"""
    visualizer = ExamVisualizer()
    
    # 生成所有可视化
    results = visualizer.generate_all_visualizations()
    
    print("\n=== 可视化分析完成 ===")
    for name, path in results.items():
        if path:
            print(f"{name}: {path}")

if __name__ == "__main__":
    main()