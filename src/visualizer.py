"""
专业可视化分析模块 - 基于扩展题目的完整数据可视化
作者: 分布式系统考试指南项目组
功能: 生成专业的统计图表、交互式网页和时间线分析
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
from typing import Dict, List, Any, Tuple
import re
from collections import Counter, defaultdict
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ExamVisualizer:
    def __init__(self):
        """初始化专业可视化分析器"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # 设置专业颜色主题
        self.colors = {
            'primary': '#1f77b4',      # 蓝色
            'secondary': '#ff7f0e',    # 橙色
            'success': '#2ca02c',      # 绿色
            'danger': '#d62728',       # 红色
            'warning': '#ff9896',      # 粉色
            'info': '#aec7e8',         # 浅蓝
            'light': '#f7f7f7',        # 浅灰
            'dark': '#2f2f2f',         # 深灰
            'timeline': [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
            ]
        }

        # 设置输出目录
        self.output_dir = Path('output/visualizations')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 存储数据
        self.extended_questions = []
        self.curriculum_data = {}
        self.questions_df = None
    
    def load_data(self, extended_questions_path: str = "output/extended_questions.json",
                  curriculum_path: str = "data/curriculum.json") -> Tuple[List[Dict], Dict]:
        """加载扩展题目数据和课程大纲"""
        try:
            # 加载扩展题目数据
            with open(extended_questions_path, 'r', encoding='utf-8') as f:
                extended_data = json.load(f)
                self.extended_questions = extended_data['questions']
                self.logger.info(f"成功加载 {len(self.extended_questions)} 个扩展题目")

            # 加载课程大纲
            with open(curriculum_path, 'r', encoding='utf-8') as f:
                self.curriculum_data = json.load(f)
                self.logger.info(f"成功加载课程大纲，包含 {len(self.curriculum_data['distributedSystemsCurriculum'])} 个章节")

            # 转换为DataFrame以便分析
            self.questions_df = pd.DataFrame(self.extended_questions)
            self.logger.info(f"数据转换完成，DataFrame形状: {self.questions_df.shape}")

            return self.extended_questions, self.curriculum_data

        except FileNotFoundError as e:
            self.logger.error(f"文件未找到: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}")
            raise

    def create_curriculum_timeline(self) -> str:
        """创建课程时间线可视化 - 水平章节布局"""
        self.logger.info("开始创建课程时间线可视化...")

        # 准备时间线数据
        timeline_data = []

        # 为每个章节创建时间段
        chapter_width = 100  # 每个章节占用的宽度

        for chapter in self.curriculum_data['distributedSystemsCurriculum']:
            chapter_number = chapter['chapterNumber']
            chapter_title = chapter['chapterTitle']
            content_items = chapter['content']

            # 找到属于此章节的所有题目
            chapter_questions = []
            for question in self.extended_questions:
                if f"Chapter {chapter_number}" in question['refer']:
                    chapter_questions.append(question)

            # 为每个知识点创建子段
            if content_items:
                content_width = chapter_width / len(content_items)

                for i, content in enumerate(content_items):
                    content_start = (int(chapter_number) - 1) * chapter_width + i * content_width
                    content_end = content_start + content_width

                    # 找到与此知识点相关的题目
                    related_questions = []
                    for question in chapter_questions:
                        if isinstance(question['knowledge_points'], list):
                            # 检查知识点匹配
                            if any(self._normalize_text(content) in self._normalize_text(kp)
                                  for kp in question['knowledge_points']):
                                related_questions.append(question)

                    timeline_data.append({
                        'Chapter': f"Chapter {chapter_number}",
                        'Chapter_Title': chapter_title,
                        'Content': content,
                        'Start': content_start,
                        'End': content_end,
                        'Questions': related_questions,
                        'Question_Count': len(related_questions),
                        'Color': self.colors['timeline'][int(chapter_number) % len(self.colors['timeline'])]
                    })

        # 创建Plotly时间线图 - 水平布局
        fig = go.Figure()

        # 添加章节背景
        for i, chapter in enumerate(self.curriculum_data['distributedSystemsCurriculum']):
            chapter_start = i * chapter_width
            chapter_end = (i + 1) * chapter_width

            fig.add_trace(go.Bar(
                x=[chapter_width],
                y=['Timeline'],
                orientation='h',
                base=[chapter_start],
                marker_color=self.colors['timeline'][i % len(self.colors['timeline'])],
                opacity=0.1,
                showlegend=False,
                hoverinfo='skip'
            ))

        # 添加知识点条
        for item in timeline_data:
            fig.add_trace(go.Bar(
                x=[item['End'] - item['Start']],
                y=['Timeline'],
                orientation='h',
                base=[item['Start']],
                marker_color=item['Color'],
                name=f"{item['Chapter']}: {item['Content']}",
                hovertemplate=f"<b>{item['Chapter']}</b><br>{item['Chapter_Title']}<br><b>{item['Content']}</b><br>相关题目: {item['Question_Count']}个<extra></extra>",
                showlegend=True
            ))

        # 添加题目标记
        for item in timeline_data:
            if item['Questions']:
                # 在知识点上方添加题目数量标记
                mid_point = (item['Start'] + item['End']) / 2

                fig.add_trace(go.Scatter(
                    x=[mid_point],
                    y=[1.1],  # 在时间线上方
                    mode='markers+text',
                    marker=dict(
                        size=max(10, min(30, item['Question_Count'] * 2)),
                        color=item['Color'],
                        symbol='circle'
                    ),
                    text=[str(item['Question_Count'])],
                    textposition="middle center",
                    textfont=dict(size=10, color='white'),
                    hovertemplate=f"<b>{item['Content']}</b><br>题目数量: {item['Question_Count']}<extra></extra>",
                    showlegend=False
                ))

        # 更新布局
        fig.update_layout(
            title={
                'text': 'NTU分布式系统课程知识点与考试题目分布时间线',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=20, color='#2f2f2f')
            },
            xaxis=dict(
                title="课程章节",
                tickmode='array',
                tickvals=[i * chapter_width + chapter_width/2 for i in range(len(self.curriculum_data['distributedSystemsCurriculum']))],
                ticktext=[f"Chapter {c['chapterNumber']}<br>{c['chapterTitle'][:20]}..."
                         for c in self.curriculum_data['distributedSystemsCurriculum']],
                showgrid=True,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False
            ),
            height=400,
            margin=dict(l=50, r=50, t=100, b=50),
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # 保存为PNG
        png_path = self.output_dir / 'curriculum_timeline.png'
        fig.write_image(str(png_path), width=1400, height=600, scale=2)
        self.logger.info(f"时间线PNG已保存: {png_path}")

        # 保存为HTML
        html_path = self.output_dir / 'curriculum_timeline.html'
        fig.write_html(str(html_path))
        self.logger.info(f"时间线HTML已保存: {html_path}")

        return str(png_path)

    def _normalize_text(self, text: str) -> str:
        """标准化文本用于匹配"""
        return text.lower().strip().replace(' ', '').replace('-', '')

    def create_question_type_analysis(self) -> str:
        """创建题型分析可视化"""
        self.logger.info("创建题型分析可视化...")

        # 统计题型分布
        type_counts = self.questions_df['type'].value_counts()

        # 创建饼图
        fig = go.Figure(data=[go.Pie(
            labels=type_counts.index,
            values=type_counts.values,
            marker_colors=self.colors['timeline'][:len(type_counts)],
            textinfo='label+percent',
            textposition='inside',
            hovertemplate="<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>"
        )])

        fig.update_layout(
            title={
                'text': '题目类型分布分析',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            font=dict(size=14),
            showlegend=False
        )

        # 保存图表
        png_path = self.output_dir / 'question_types_pie.png'
        fig.write_image(str(png_path), width=800, height=600, scale=2)

        return str(png_path)

    def create_knowledge_points_heatmap(self) -> str:
        """创建知识点热力图"""
        self.logger.info("创建知识点热力图...")

        # 统计知识点与章节的关系
        kp_chapter_matrix = defaultdict(lambda: defaultdict(int))

        for question in self.extended_questions:
            chapter = question['refer'].split(',')[0].strip()  # 取第一个章节
            if isinstance(question['knowledge_points'], list):
                for kp in question['knowledge_points']:
                    kp_chapter_matrix[kp][chapter] += 1

        # 转换为DataFrame
        df_heatmap = pd.DataFrame(kp_chapter_matrix).fillna(0).T

        # 创建热力图
        fig = go.Figure(data=go.Heatmap(
            z=df_heatmap.values,
            x=df_heatmap.columns,
            y=df_heatmap.index,
            colorscale='Blues',
            hoverongaps=False,
            hovertemplate='知识点: %{y}<br>章节: %{x}<br>题目数: %{z}<extra></extra>'
        ))

        fig.update_layout(
            title='知识点与章节关系热力图',
            xaxis_title='章节',
            yaxis_title='知识点',
            height=600
        )

        # 保存图表
        png_path = self.output_dir / 'knowledge_points_heatmap.png'
        fig.write_image(str(png_path), width=1000, height=600, scale=2)

        return str(png_path)

    def create_chapter_importance_chart(self) -> str:
        """创建章节重要性分析图表"""
        self.logger.info("创建章节重要性分析图表...")

        # 统计各章节的题目数量
        chapter_counts = defaultdict(int)
        for question in self.extended_questions:
            chapters = question['refer'].split(',')
            for chapter in chapters:
                chapter = chapter.strip()
                chapter_counts[chapter] += 1

        # 排序
        sorted_chapters = sorted(chapter_counts.items(), key=lambda x: x[1], reverse=True)
        chapters, counts = zip(*sorted_chapters)

        # 创建柱状图
        fig = go.Figure(data=[go.Bar(
            x=chapters,
            y=counts,
            marker_color=self.colors['timeline'][:len(chapters)],
            text=counts,
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>题目数量: %{y}<extra></extra>'
        )])

        fig.update_layout(
            title='各章节题目数量统计',
            xaxis_title='章节',
            yaxis_title='题目数量',
            height=500
        )

        # 保存图表
        png_path = self.output_dir / 'chapter_importance.png'
        fig.write_image(str(png_path), width=1000, height=500, scale=2)

        return str(png_path)

    def create_comprehensive_dashboard(self) -> str:
        """创建综合数据分析网页 - 多维度专业分析"""
        self.logger.info("创建综合数据分析网页...")

        # 准备各种统计数据
        stats_data = self._prepare_dashboard_stats()

        # 创建各个图表的JSON数据
        charts_data = {
            'question_types': self._create_question_types_chart_data(),
            'chapter_distribution': self._create_chapter_distribution_data(),
            'knowledge_points_analysis': self._create_knowledge_points_analysis_data(),
            'difficulty_analysis': self._create_difficulty_analysis_data(),
            'temporal_distribution': self._create_temporal_distribution_data()
        }

        # 创建HTML内容
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NTU分布式系统考试分析仪表板</title>
    <script src="https://cdn.plotly.com/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        .dashboard-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }}
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .stats-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-number {{
            font-size: 3em;
            font-weight: bold;
            color: {self.colors['primary']};
            margin-bottom: 10px;
        }}
        .stat-label {{
            font-size: 1.1em;
            color: #666;
            margin-bottom: 5px;
        }}
        .stat-trend {{
            font-size: 0.9em;
            color: {self.colors['success']};
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        .chart-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .chart-title {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }}
        .chart-description {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }}
        .full-width-chart {{
            grid-column: 1 / -1;
            margin-bottom: 30px;
        }}
        .insights-section {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }}
        .insights-title {{
            font-size: 2em;
            margin-bottom: 20px;
            color: #333;
        }}
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .insight-card {{
            background: linear-gradient(135deg, {self.colors['info']}, {self.colors['primary']});
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .insight-title {{
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .footer {{
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .tab-container {{
            margin-bottom: 20px;
        }}
        .tab-buttons {{
            display: flex;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 5px;
            margin-bottom: 20px;
        }}
        .tab-btn {{
            flex: 1;
            padding: 10px 20px;
            border: none;
            background: transparent;
            color: rgba(255, 255, 255, 0.7);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .tab-btn.active {{
            background: white;
            color: #333;
            font-weight: bold;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        @media (max-width: 768px) {{
            .dashboard-container {{
                padding: 10px;
            }}
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            .stats-overview {{
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Header -->
        <div class="header">
            <h1>🎓 NTU分布式系统考试分析仪表板</h1>
            <p>基于153个扩展题目的多维度专业分析报告</p>
        </div>

        <!-- Statistics Overview -->
        <div class="stats-overview">
            <div class="stat-card">
                <div class="stat-number">{stats_data['total_questions']}</div>
                <div class="stat-label">总题目数量</div>
                <div class="stat-trend">扩展后题目</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats_data['unique_knowledge_points']}</div>
                <div class="stat-label">知识点覆盖</div>
                <div class="stat-trend">全面覆盖</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats_data['question_types_count']}</div>
                <div class="stat-label">题型种类</div>
                <div class="stat-trend">多样化</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats_data['chapters_covered']}</div>
                <div class="stat-label">章节覆盖</div>
                <div class="stat-trend">完整课程</div>
            </div>
        </div>

        <!-- Charts Section -->
        <div class="charts-grid">
            <!-- Question Types Chart -->
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title">📊 题型分布分析</div>
                </div>
                <div class="chart-description">
                    分析不同题型的分布情况，帮助了解考试重点题型
                </div>
                <div id="question-types-chart"></div>
            </div>

            <!-- Chapter Distribution -->
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title">📚 章节题目分布</div>
                </div>
                <div class="chart-description">
                    各章节题目数量统计，识别重点章节
                </div>
                <div id="chapter-distribution-chart"></div>
            </div>

            <!-- Knowledge Points Analysis -->
            <div class="chart-card full-width-chart">
                <div class="chart-header">
                    <div class="chart-title">🎯 知识点重要性分析</div>
                </div>
                <div class="chart-description">
                    基于题目数量的知识点重要性排名
                </div>
                <div id="knowledge-points-chart"></div>
            </div>

            <!-- Difficulty Analysis -->
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title">📈 难度分析</div>
                </div>
                <div class="chart-description">
                    基于题型和知识点复杂度的难度评估
                </div>
                <div id="difficulty-chart"></div>
            </div>

            <!-- Temporal Distribution -->
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title">⏰ 时间分布</div>
                </div>
                <div class="chart-description">
                    题目在课程时间线上的分布
                </div>
                <div id="temporal-chart"></div>
            </div>
        </div>

        <!-- Insights Section -->
        <div class="insights-section">
            <div class="insights-title">💡 关键洞察</div>
            <div class="insights-grid">
                <div class="insight-card">
                    <div class="insight-title">🏆 重点章节</div>
                    <div>{stats_data['top_chapter']}</div>
                </div>
                <div class="insight-card">
                    <div class="insight-title">🎯 高频知识点</div>
                    <div>{stats_data['top_knowledge_point']}</div>
                </div>
                <div class="insight-card">
                    <div class="insight-title">📝 主要题型</div>
                    <div>{stats_data['dominant_type']}</div>
                </div>
                <div class="insight-card">
                    <div class="insight-title">📊 覆盖率</div>
                    <div>{stats_data['coverage_rate']}</div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>© 2024 NTU分布式系统考试指南项目组 | 数据驱动的学习分析</p>
        </div>
    </div>

    <script>
        // 题型分布图表
        const questionTypesData = {charts_data['question_types']};
        Plotly.newPlot('question-types-chart', questionTypesData.data, questionTypesData.layout);

        // 章节分布图表
        const chapterData = {charts_data['chapter_distribution']};
        Plotly.newPlot('chapter-distribution-chart', chapterData.data, chapterData.layout);

        // 知识点分析图表
        const knowledgeData = {charts_data['knowledge_points_analysis']};
        Plotly.newPlot('knowledge-points-chart', knowledgeData.data, knowledgeData.layout);

        // 难度分析图表
        const difficultyData = {charts_data['difficulty_analysis']};
        Plotly.newPlot('difficulty-chart', difficultyData.data, difficultyData.layout);

        // 时间分布图表
        const temporalData = {charts_data['temporal_distribution']};
        Plotly.newPlot('temporal-chart', temporalData.data, temporalData.layout);
    </script>
</body>
</html>
"""

        # 保存HTML文件
        html_path = self.output_dir / 'comprehensive_dashboard.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"综合分析网页已保存: {html_path}")
        return str(html_path)
    
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
        for kp_data in df['knowledge_points'].dropna():
            if isinstance(kp_data, list):
                # 如果是列表格式
                points = [kp.strip() for kp in kp_data if kp.strip() and kp.strip() != 'Uncategorized']
                all_knowledge_points.extend(points)
            elif isinstance(kp_data, str) and kp_data != '未识别' and kp_data != 'Uncategorized':
                # 如果是字符串格式（向后兼容）
                points = [kp.strip() for kp in kp_data.split(';') if kp.strip()]
                all_knowledge_points.extend(points)
        
        # 统计知识点频率
        kp_counter = Counter(all_knowledge_points)
        
        analysis = {
            'total_unique_points': len(kp_counter),
            'top_10_points': dict(kp_counter.most_common(10)),
            'total_mentions': sum(kp_counter.values()),
            'coverage_rate': len([kp for kp in df['knowledge_points'] 
                                 if isinstance(kp, list) and kp and kp != ['Uncategorized']]) / len(df)
        }
        
        return analysis
    
    def analyze_chapter_importance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析章节重要程度和题型分布"""
        # 章节映射
        chapter_mapping = {
            '第1章': 'Characterization of Distributed Systems & System Models',
            '第2章': 'Interprocess Communication', 
            '第3章': 'Distributed Objects & Remote Invocation',
            '第4章': 'Distributed File Systems',
            '第5章': 'Peer-to-Peer File Sharing Systems',
            '第6章': 'Name Services',
            '第7章': 'Time and Global States'
        }
        
        # 统计每个章节的题目数量
        chapter_counts = {}
        chapter_type_distribution = {}
        
        for chapter_num, chapter_name in chapter_mapping.items():
            # 找到该章节的题目
            chapter_questions = df[df['refer'].str.contains(chapter_num, na=False)]
            chapter_counts[chapter_num] = len(chapter_questions)
            
            # 统计该章节的题型分布
            if not chapter_questions.empty:
                type_counts = chapter_questions['type'].value_counts().to_dict()
                chapter_type_distribution[chapter_num] = type_counts
            else:
                chapter_type_distribution[chapter_num] = {}
        
        analysis = {
            'chapter_counts': chapter_counts,
            'chapter_type_distribution': chapter_type_distribution,
            'total_chapters': len(chapter_mapping),
            'most_important_chapter': max(chapter_counts, key=chapter_counts.get) if chapter_counts else None,
            'least_important_chapter': min(chapter_counts, key=chapter_counts.get) if chapter_counts else None
        }
        
        return analysis
    
    def plot_chapter_importance_analysis(self, df: pd.DataFrame) -> str:
        """绘制章节重要程度和题型分布分析图"""
        chapter_analysis = self.analyze_chapter_importance(df)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
        
        # 1. 章节重要程度条形图
        chapters = list(chapter_analysis['chapter_counts'].keys())
        counts = list(chapter_analysis['chapter_counts'].values())
        
        bars = ax1.bar(range(len(chapters)), counts, 
                      color=self.colors['primary'], alpha=0.7, edgecolor='black', linewidth=1)
        ax1.set_title('各章节题目数量分布 (章节重要程度)', fontsize=16, fontweight='bold', pad=20)
        ax1.set_xlabel('章节', fontsize=12)
        ax1.set_ylabel('题目数量', fontsize=12)
        ax1.set_xticks(range(len(chapters)))
        ax1.set_xticklabels(chapters, rotation=45, ha='right')
        ax1.grid(axis='y', alpha=0.3)
        
        # 在柱子上添加数值标签
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(count)}', ha='center', va='bottom', fontweight='bold')
        
        # 2. 章节题型分布堆叠图
        chapter_types = chapter_analysis['chapter_type_distribution']
        all_types = set()
        for types_dict in chapter_types.values():
            all_types.update(types_dict.keys())
        all_types = sorted(list(all_types))
        
        # 准备堆叠数据
        bottom_values = [0] * len(chapters)
        colors = [self.colors['primary'], self.colors['secondary'], self.colors['accent'], 
                 self.colors['success'], self.colors['warning'], self.colors['info']]
        
        for i, question_type in enumerate(all_types):
            values = [chapter_types[chap].get(question_type, 0) for chap in chapters]
            ax2.bar(range(len(chapters)), values, bottom=bottom_values, 
                   label=question_type, color=colors[i % len(colors)], alpha=0.8)
            bottom_values = [bottom + value for bottom, value in zip(bottom_values, values)]
        
        ax2.set_title('各章节题型分布', fontsize=16, fontweight='bold', pad=20)
        ax2.set_xlabel('章节', fontsize=12)
        ax2.set_ylabel('题目数量', fontsize=12)
        ax2.set_xticks(range(len(chapters)))
        ax2.set_xticklabels(chapters, rotation=45, ha='right')
        ax2.legend(title='题型', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图片
        output_path = self.output_dir / 'chapter_importance_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"章节重要程度分析图已保存: {output_path}")
        return str(output_path)
    
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
    
    def plot_chapter_distribution(self, df: pd.DataFrame) -> str:
        """绘制章节考试占比分析图"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('分布式系统考试章节分析报告', fontsize=16, fontweight='bold')
        
        # 1. 章节题目数量分布（饼图）
        chapter_counts = df['refer'].value_counts()
        
        # 简化章节名称显示
        simplified_names = []
        for chapter in chapter_counts.index:
            if 'Chapter' in chapter:
                # 提取章节号和关键词
                parts = chapter.split('Chapter')[1].strip()
                if ' ' in parts:
                    chapter_num = parts.split(' ')[0]
                    keywords = parts.split(' ')[-3:]  # 取最后3个关键词
                    simplified_names.append(f"Ch{chapter_num} {' '.join(keywords)}")
                else:
                    simplified_names.append(f"Ch{parts}")
            else:
                simplified_names.append(chapter[:20] + '...' if len(chapter) > 20 else chapter)
        
        colors = plt.cm.Set3(range(len(chapter_counts)))
        wedges, texts, autotexts = ax1.pie(chapter_counts.values, 
                                          labels=simplified_names,
                                          autopct='%1.1f%%', 
                                          startangle=90,
                                          colors=colors)
        ax1.set_title('章节题目数量占比', fontsize=12, fontweight='bold')
        
        # 2. 章节题目数量（柱状图）
        bars = ax2.bar(range(len(chapter_counts)), chapter_counts.values, 
                      color=colors[:len(chapter_counts)])
        ax2.set_title('各章节题目数量分布', fontsize=12, fontweight='bold')
        ax2.set_xlabel('章节')
        ax2.set_ylabel('题目数量')
        ax2.set_xticks(range(len(chapter_counts)))
        ax2.set_xticklabels(simplified_names, rotation=45, ha='right')
        
        # 在柱状图上添加数值标签
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}',
                    ha='center', va='bottom', fontweight='bold')
        
        # 3. 章节vs题型分布（堆叠柱状图）
        chapter_type_crosstab = pd.crosstab(df['refer'], df['type'])
        chapter_type_crosstab.plot(kind='bar', stacked=True, ax=ax3, 
                                  color=self.colors['palette'][:len(chapter_type_crosstab.columns)])
        ax3.set_title('章节题型分布', fontsize=12, fontweight='bold')
        ax3.set_xlabel('章节')
        ax3.set_ylabel('题目数量')
        ax3.tick_params(axis='x', rotation=45)
        ax3.legend(title='题型', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 4. 章节重要度分析（基于题目数量和平均长度）
        chapter_stats = df.groupby('refer').agg({
            'title_length': ['mean', 'count'],
            'type': 'nunique'
        }).round(1)
        
        chapter_stats.columns = ['平均题目长度', '题目数量', '题型种类']
        chapter_stats['重要度得分'] = (
            chapter_stats['题目数量'] * 0.5 + 
            chapter_stats['题型种类'] * 0.3 + 
            (chapter_stats['平均题目长度'] / 100) * 0.2
        ).round(2)
        
        # 绘制重要度气泡图
        x = chapter_stats['题目数量']
        y = chapter_stats['平均题目长度']
        sizes = chapter_stats['重要度得分'] * 100
        
        scatter = ax4.scatter(x, y, s=sizes, alpha=0.6, c=range(len(chapter_stats)), 
                            cmap='viridis')
        ax4.set_title('章节重要度分析', fontsize=12, fontweight='bold')
        ax4.set_xlabel('题目数量')
        ax4.set_ylabel('平均题目长度')
        
        # 添加章节标签
        for i, (idx, row) in enumerate(chapter_stats.iterrows()):
            chapter_short = simplified_names[list(chapter_counts.index).index(idx)] if idx in chapter_counts.index else str(idx)[:10]
            ax4.annotate(chapter_short, 
                        (row['题目数量'], row['平均题目长度']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8, alpha=0.8)
        
        plt.tight_layout()
        
        # 保存图片
        output_path = self.output_dir / 'chapter_distribution_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"章节分布分析图已保存: {output_path}")
        
        # 打印详细统计
        print("\n📚 章节详细统计:")
        print("=" * 60)
        for chapter, count in chapter_counts.items():
            percentage = count / len(df) * 100
            print(f"{chapter[:50]:50} {count:3d}题 ({percentage:5.1f}%)")
        
        return str(output_path)
    
    def plot_chapter_importance_analysis(self, df: pd.DataFrame) -> str:
        """绘制章节重要程度和题型分布分析图 - 为了百万年薪！"""
        # 分析refer字段，提取章节信息
        chapter_data = []
        
        for _, row in df.iterrows():
            refer = str(row.get('refer', ''))
            question_type = str(row.get('type', ''))
            
            # 从refer中提取章节号 - 支持英文格式
            chapter_match = re.search(r'Chapter\s+(\d+)', refer, re.IGNORECASE)
            if not chapter_match:
                # 也支持中文格式
                chapter_match = re.search(r'第(\d+)章', refer)
            
            if chapter_match:
                chapter_num = int(chapter_match.group(1))
                chapter_data.append({
                    'chapter': chapter_num,
                    'type': question_type,
                    'refer': refer
                })
            else:
                # 如果没有找到章节号，使用refer的前20个字符作为标识
                chapter_data.append({
                    'chapter': refer[:20] + '...' if len(refer) > 20 else refer,
                    'type': question_type,
                    'refer': refer
                })
        
        if not chapter_data:
            self.logger.warning("没有找到章节相关数据")
            return ""
        
        # 转换为DataFrame
        chapter_df = pd.DataFrame(chapter_data)
        
        # 统计每个章节的题目数量 - 处理混合数据类型
        chapter_counts = chapter_df['chapter'].value_counts()
        # 分别处理数字和字符串章节
        numeric_chapters = {}
        string_chapters = {}
        
        for chapter, count in chapter_counts.items():
            if isinstance(chapter, int):
                numeric_chapters[chapter] = count
            else:
                string_chapters[chapter] = count
        
        # 先按数字章节排序，再添加字符串章节
        sorted_chapters = {}
        if numeric_chapters:
            for ch in sorted(numeric_chapters.keys()):
                sorted_chapters[ch] = numeric_chapters[ch]
        if string_chapters:
            for ch in sorted(string_chapters.keys()):
                sorted_chapters[ch] = string_chapters[ch]
        
        chapter_counts = pd.Series(sorted_chapters)
        
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
        for kp_data in df['knowledge_points'].dropna():
            if isinstance(kp_data, list):
                # 如果是列表格式
                points = [kp.strip() for kp in kp_data if kp.strip() and kp.strip() != 'Uncategorized']
                all_knowledge_points.extend(points)
            elif isinstance(kp_data, str) and kp_data != '未识别' and kp_data != 'Uncategorized':
                # 如果是字符串格式（向后兼容）
                points = [kp.strip() for kp in kp_data.split(';') if kp.strip()]
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
            kp_data = row['knowledge_points']
            if isinstance(kp_data, list):
                # 列表格式
                if not kp_data or kp_data == ['Uncategorized']:
                    coverage_data.append('未识别')
                else:
                    kp_count = len([kp for kp in kp_data if kp.strip() and kp.strip() != 'Uncategorized'])
                    if kp_count == 0:
                        coverage_data.append('未识别')
                    elif kp_count == 1:
                        coverage_data.append('单个知识点')
                    elif kp_count <= 3:
                        coverage_data.append('2-3个知识点')
                    else:
                        coverage_data.append('4+个知识点')
            elif isinstance(kp_data, str):
                # 字符串格式（向后兼容）
                if kp_data == '未识别' or kp_data == 'Uncategorized' or pd.isna(kp_data):
                    coverage_data.append('未识别')
                else:
                    kp_count = len([kp.strip() for kp in kp_data.split(';')])
                    if kp_count == 1:
                        coverage_data.append('单个知识点')
                    elif kp_count <= 3:
                        coverage_data.append('2-3个知识点')
                    else:
                        coverage_data.append('4+个知识点')
            else:
                coverage_data.append('未识别')
        
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
        
        # 题型分布
        type_counts = df['type'].value_counts()
        fig.add_trace(
            go.Bar(x=type_counts.index, y=type_counts.values,
                   name="题型分布", marker_color=self.colors['secondary']),
            row=2, col=1
        )
        
        # 题目长度分布散点图
        fig.add_trace(
            go.Scatter(x=df.index, y=df['title_length'],
                      mode='markers', name="题目长度分布",
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
                'knowledge_coverage': len([kp for kp in df['knowledge_points'] 
                                         if isinstance(kp, list) and kp and kp != ['Uncategorized']]) / len(df) * 100
            },
            'type_analysis': self.analyze_question_types(df),
            'knowledge_analysis': self.analyze_knowledge_points(df),
            'difficulty_analysis': {
                'avg_title_length': df['title_length'].mean(),
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
        for kp_data in df['knowledge_points'].dropna():
            if isinstance(kp_data, list):
                # 列表格式
                all_kp.extend([kp.strip() for kp in kp_data if kp.strip() and kp.strip() != 'Uncategorized'])
            elif isinstance(kp_data, str) and kp_data != '未识别' and kp_data != 'Uncategorized':
                # 字符串格式（向后兼容）
                all_kp.extend([kp.strip() for kp in kp_data.split(';')])
        
        if all_kp:
            kp_counter = Counter(all_kp)
            top_kp = kp_counter.most_common(3)
            recommendations.append(f"高频知识点：{', '.join([kp[0] for kp in top_kp])}")
        
        # 基于题目复杂度的建议
        avg_length = df['title_length'].mean()
        if avg_length > 500:
            recommendations.append("题目普遍较长，建议加强理解能力训练")
        
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
    
    def generate_all_visualizations(self) -> Dict[str, str]:
        """生成所有专业可视化图表"""
        # 加载数据
        try:
            self.load_data()
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            return {}

        # 生成各种图表
        results = {}

        try:
            # 课程时间线
            results['curriculum_timeline'] = self.create_curriculum_timeline()

            # 题型分析
            results['question_types'] = self.create_question_type_analysis()

            # 知识点热力图
            results['knowledge_heatmap'] = self.create_knowledge_points_heatmap()

            # 章节重要性
            results['chapter_importance'] = self.create_chapter_importance_chart()

            # 综合仪表板
            results['comprehensive_dashboard'] = self.create_comprehensive_dashboard()

            self.logger.info("所有专业可视化图表生成完成")
            return results

        except Exception as e:
            self.logger.error(f"可视化生成失败: {e}")
            return results
            
        except Exception as e:
            self.logger.error(f"可视化生成过程中出现错误: {e}")
        
        return results

    def _prepare_dashboard_stats(self) -> Dict[str, Any]:
        """准备仪表板统计数据"""
        # 计算基础统计
        total_questions = len(self.extended_questions)
        question_types = [q['type'] for q in self.extended_questions]
        unique_types = set(question_types)
        question_types_count = len(unique_types)

        # 知识点统计
        all_knowledge_points = []
        for q in self.extended_questions:
            if isinstance(q['knowledge_points'], list):
                all_knowledge_points.extend(q['knowledge_points'])
        unique_knowledge_points = len(set(all_knowledge_points))

        # 章节统计
        chapter_stats = defaultdict(int)
        for q in self.extended_questions:
            chapters = q['refer'].split(',')
            for chapter in chapters:
                chapter_stats[chapter.strip()] += 1
        chapters_covered = len(chapter_stats)

        # 找出重点章节和知识点
        top_chapter = max(chapter_stats.items(), key=lambda x: x[1])[0] if chapter_stats else "N/A"
        knowledge_point_counts = Counter(all_knowledge_points)
        top_knowledge_point = knowledge_point_counts.most_common(1)[0][0] if knowledge_point_counts else "N/A"

        # 主要题型
        type_counts = Counter(question_types)
        dominant_type = type_counts.most_common(1)[0][0] if type_counts else "N/A"

        # 覆盖率计算
        total_curriculum_kps = sum(len(chapter['content']) for chapter in self.curriculum_data['distributedSystemsCurriculum'])
        coverage_rate = f"{unique_knowledge_points}/{total_curriculum_kps} ({unique_knowledge_points/total_curriculum_kps*100:.1f}%)"

        return {
            'total_questions': total_questions,
            'unique_knowledge_points': unique_knowledge_points,
            'question_types_count': question_types_count,
            'chapters_covered': chapters_covered,
            'top_chapter': top_chapter,
            'top_knowledge_point': top_knowledge_point,
            'dominant_type': dominant_type,
            'coverage_rate': coverage_rate
        }

    def _create_question_types_chart_data(self) -> Dict[str, Any]:
        """创建题型分布图表数据"""
        type_counts = Counter(q['type'] for q in self.extended_questions)
        types, counts = zip(*type_counts.items())

        return {
            'data': [{
                'type': 'pie',
                'labels': types,
                'values': counts,
                'marker': {
                    'colors': self.colors['timeline'][:len(types)]
                },
                'textinfo': 'label+percent',
                'hovertemplate': '<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>'
            }],
            'layout': {
                'height': 400,
                'margin': {'t': 0, 'b': 0, 'l': 0, 'r': 0}
            }
        }

    def _create_chapter_distribution_data(self) -> Dict[str, Any]:
        """创建章节分布图表数据"""
        chapter_stats = defaultdict(int)
        for q in self.extended_questions:
            chapters = q['refer'].split(',')
            for chapter in chapters:
                chapter_stats[chapter.strip()] += 1

        chapters, counts = zip(*sorted(chapter_stats.items(), key=lambda x: x[1], reverse=True))

        return {
            'data': [{
                'type': 'bar',
                'x': chapters,
                'y': counts,
                'marker': {
                    'color': self.colors['timeline'][:len(chapters)]
                },
                'text': counts,
                'textposition': 'auto',
                'hovertemplate': '<b>%{x}</b><br>题目数量: %{y}<extra></extra>'
            }],
            'layout': {
                'height': 400,
                'xaxis': {'title': '章节'},
                'yaxis': {'title': '题目数量'},
                'margin': {'t': 20, 'b': 50, 'l': 50, 'r': 20}
            }
        }

    def _create_knowledge_points_analysis_data(self) -> Dict[str, Any]:
        """创建知识点分析图表数据"""
        all_knowledge_points = []
        for q in self.extended_questions:
            if isinstance(q['knowledge_points'], list):
                all_knowledge_points.extend(q['knowledge_points'])

        kp_counts = Counter(all_knowledge_points)
        kps, counts = zip(*kp_counts.most_common(20))  # Top 20

        return {
            'data': [{
                'type': 'bar',
                'x': counts,
                'y': kps,
                'orientation': 'h',
                'marker': {
                    'color': self.colors['primary']
                },
                'hovertemplate': '<b>%{y}</b><br>题目数量: %{x}<extra></extra>'
            }],
            'layout': {
                'height': 600,
                'xaxis': {'title': '题目数量'},
                'yaxis': {'title': '知识点', 'autorange': 'reversed'},
                'margin': {'t': 20, 'b': 50, 'l': 200, 'r': 20}
            }
        }

    def _create_difficulty_analysis_data(self) -> Dict[str, Any]:
        """创建难度分析图表数据"""
        # 基于题型和知识点数量估算难度
        difficulty_scores = []
        for q in self.extended_questions:
            score = 0
            # 题型难度权重
            type_weights = {
                'Calculation': 3,
                'Essay': 4,
                'Programming': 5,
                'Short Answer': 2,
                'Fill in Blank': 1
            }
            score += type_weights.get(q['type'], 2)

            # 知识点数量影响难度
            if isinstance(q['knowledge_points'], list):
                score += len(q['knowledge_points']) * 0.5

            difficulty_scores.append(score)

        # 难度分布
        bins = [0, 2, 3, 4, 5, 10]
        labels = ['简单', '中等', '稍难', '困难', '极难']
        hist, bin_edges = np.histogram(difficulty_scores, bins=bins)

        return {
            'data': [{
                'type': 'bar',
                'x': labels,
                'y': hist,
                'marker': {
                    'color': ['#2ca02c', '#ff7f0e', '#ff9896', '#d62728', '#9467bd']
                },
                'text': hist,
                'textposition': 'auto',
                'hovertemplate': '<b>%{x}</b><br>题目数量: %{y}<extra></extra>'
            }],
            'layout': {
                'height': 400,
                'xaxis': {'title': '难度等级'},
                'yaxis': {'title': '题目数量'},
                'margin': {'t': 20, 'b': 50, 'l': 50, 'r': 20}
            }
        }

    def _create_temporal_distribution_data(self) -> Dict[str, Any]:
        """创建时间分布图表数据"""
        # 按章节统计题目分布
        chapter_timeline = defaultdict(int)
        for q in self.extended_questions:
            chapters = q['refer'].split(',')
            for chapter in chapters:
                chapter_timeline[chapter.strip()] += 1

        chapters, counts = zip(*sorted(chapter_timeline.items()))

        return {
            'data': [{
                'type': 'scatter',
                'mode': 'lines+markers',
                'x': chapters,
                'y': counts,
                'line': {'color': self.colors['primary'], 'width': 3},
                'marker': {'size': 8, 'color': self.colors['secondary']},
                'hovertemplate': '<b>%{x}</b><br>题目数量: %{y}<extra></extra>'
            }],
            'layout': {
                'height': 400,
                'xaxis': {'title': '章节'},
                'yaxis': {'title': '题目数量'},
                'margin': {'t': 20, 'b': 50, 'l': 50, 'r': 20}
            }
        }

    def _create_correlation_analysis_data(self) -> Dict[str, Any]:
        """创建相关性分析数据"""
        # 这里可以添加更复杂的相关性分析
        return {}

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