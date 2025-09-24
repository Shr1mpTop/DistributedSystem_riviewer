// Vue.js 应用
const { createApp } = Vue;

createApp({
    data() {
        return {
            curriculumData: null,
            questionsData: null,
            loading: true,
            error: null,
            showModal: false,
            modalTitle: '',
            modalContent: [],
            stats: []
        }
    },

    mounted() {
        this.initApp();
    },

    methods: {
        async initApp() {
            try {
                console.log('开始加载数据...');

                // 并行加载所有数据
                const [curriculumResponse, questionsResponse] = await Promise.all([
                    this.fetchData('/api/curriculum'),
                    this.fetchData('/api/questions')
                ]);

                this.curriculumData = curriculumResponse.data;
                this.questionsData = questionsResponse.data;

                console.log('课程数据加载成功:', this.curriculumData);
                console.log('题目数据加载成功:', this.questionsData);

                // 生成统计数据
                this.generateStats();

                // 创建所有可视化图表
                this.$nextTick(() => {
                    setTimeout(() => {
                        this.createTimeline();
                        this.createQuestionTypesChart();
                        this.createKnowledgeHeatmap();
                        this.createChapterImportanceChart();
                        this.createDifficultyDistributionChart();
                    }, 100);
                });

                this.loading = false;
                console.log('应用初始化完成');

            } catch (error) {
                console.error('数据加载失败:', error);
                this.error = error.message;
                this.loading = false;
            }
        },

        // 通用数据获取方法
        async fetchData(endpoint) {
            const response = await fetch(`http://localhost:3001${endpoint}`);
            if (!response.ok) {
                throw new Error(`API请求失败: ${response.status} ${response.statusText}`);
            }
            return await response.json();
        },

        // 生成统计数据
        async generateStats() {
            try {
                const statsResponse = await this.fetchData('/api/statistics');
                const statsData = statsResponse.data;

                this.stats = [
                    { number: statsData.totalQuestions, label: '总题目数量' },
                    { number: statsData.uniqueTypes, label: '题型种类' },
                    { number: statsData.uniqueKnowledgePoints, label: '知识点覆盖' },
                    { number: statsData.chaptersCovered, label: '章节覆盖' }
                ];
            } catch (error) {
                console.error('获取统计数据失败:', error);
                // 降级到本地计算
                this.generateStatsLocally();
            }
        },

        // 本地计算统计数据（降级方案）
        generateStatsLocally() {
            const questions = this.questionsData.questions;
            const totalQuestions = questions.length;
            const uniqueTypes = new Set(questions.map(q => q.type)).size;

            // 计算知识点数量
            const allKnowledgePoints = new Set();
            questions.forEach(q => {
                if (q.knowledge_points && Array.isArray(q.knowledge_points)) {
                    q.knowledge_points.forEach(kp => allKnowledgePoints.add(kp));
                }
            });
            const uniqueKnowledgePoints = allKnowledgePoints.size;

            // 计算章节覆盖
            const chapters = new Set();
            questions.forEach(q => {
                if (q.refer) {
                    const chapterMatches = q.refer.match(/Chapter (\d+)/g);
                    if (chapterMatches) {
                        chapterMatches.forEach(match => {
                            const chapterNum = match.match(/Chapter (\d+)/)[1];
                            chapters.add(chapterNum);
                        });
                    }
                }
            });
            const chaptersCovered = chapters.size;

            this.stats = [
                { number: totalQuestions, label: '总题目数量' },
                { number: uniqueTypes, label: '题型种类' },
                { number: uniqueKnowledgePoints, label: '知识点覆盖' },
                { number: chaptersCovered, label: '章节覆盖' }
            ];
        },

        // 创建时间线
        createTimeline() {
            const chapters = this.curriculumData.distributedSystemsCurriculum;
            const questions = this.questionsData.questions;

            // 准备时间线数据
            const timelineData = [];
            const chapterWidth = 100;

            chapters.forEach((chapter, chapterIndex) => {
                const chapterNumber = chapter.chapterNumber;
                const chapterTitle = chapter.chapterTitle;
                const contentItems = chapter.content;

                if (contentItems && contentItems.length > 0) {
                    const contentWidth = chapterWidth / contentItems.length;

                    contentItems.forEach((content, contentIndex) => {
                        const contentStart = chapterIndex * chapterWidth + contentIndex * contentWidth;
                        const contentEnd = contentStart + contentWidth;

                        // 找到与此知识点相关的题目
                        const relatedQuestions = questions.filter(question => {
                            if (!question.knowledge_points || !Array.isArray(question.knowledge_points)) {
                                return false;
                            }
                            return question.knowledge_points.some(kp =>
                                this.normalizeText(content).includes(this.normalizeText(kp)) ||
                                this.normalizeText(kp).includes(this.normalizeText(content))
                            );
                        });

                        timelineData.push({
                            chapter: `Chapter ${chapterNumber}`,
                            chapterTitle: chapterTitle,
                            content: content,
                            start: contentStart,
                            end: contentEnd,
                            questions: relatedQuestions,
                            questionCount: relatedQuestions.length,
                            color: this.getChapterColor(chapterIndex)
                        });
                    });
                }
            });

            // 创建Plotly图表
            const fig = {
                data: [],
                layout: {
                    title: '',
                    xaxis: {
                        title: '课程进度',
                        showgrid: false,
                        zeroline: false,
                        showticklabels: false
                    },
                    yaxis: {
                        showgrid: false,
                        zeroline: false,
                        showticklabels: false
                    },
                    showlegend: false,
                    height: 400,
                    margin: { l: 50, r: 50, t: 50, b: 50 }
                }
            };

            // 添加章节背景
            chapters.forEach((chapter, index) => {
                const chapterStart = index * chapterWidth;
                const chapterEnd = (index + 1) * chapterWidth;

                fig.data.push({
                    type: 'bar',
                    orientation: 'h',
                    x: [chapterWidth],
                    y: ['Timeline'],
                    base: [chapterStart],
                    marker: {
                        color: this.getChapterColor(index),
                        opacity: 0.1
                    },
                    showlegend: false,
                    hoverinfo: 'skip'
                });
            });

            // 添加知识点条
            timelineData.forEach(item => {
                fig.data.push({
                    type: 'bar',
                    orientation: 'h',
                    x: [item.end - item.start],
                    y: ['Timeline'],
                    base: [item.start],
                    marker: {
                        color: item.color,
                        opacity: 0.7
                    },
                    name: `${item.chapter}: ${item.content}`,
                    hovertemplate: `<b>${item.chapter}</b><br>${item.chapterTitle}<br><b>${item.content}</b><br>相关题目: ${item.questionCount}个<extra></extra>`,
                    showlegend: true
                });
            });

            // 添加题目标记气泡
            timelineData.forEach(item => {
                if (item.questionCount > 0) {
                    const midPoint = (item.start + item.end) / 2;
                    const bubbleSize = Math.max(20, Math.min(50, item.questionCount * 3));

                    fig.data.push({
                        type: 'scatter',
                        mode: 'markers+text',
                        x: [midPoint],
                        y: [1.1],
                        text: [item.questionCount.toString()],
                        textposition: 'middle center',
                        textfont: {
                            size: Math.max(10, Math.min(16, bubbleSize / 2)),
                            color: 'white',
                            weight: 'bold'
                        },
                        marker: {
                            size: bubbleSize,
                            color: item.color,
                            opacity: 0.8,
                            line: {
                                color: 'white',
                                width: 2
                            }
                        },
                        hovertemplate: `<b>${item.content}</b><br>题目数量: ${item.questionCount}个<br>点击查看详情<extra></extra>`,
                        customdata: [item],
                        showlegend: false
                    });
                }
            });

            // 渲染图表
            Plotly.newPlot('timeline', fig.data, fig.layout);

            // 添加点击事件
            document.getElementById('timeline').on('plotly_click', (data) => {
                if (data.points && data.points[0] && data.points[0].customdata && data.points[0].customdata[0]) {
                    const item = data.points[0].customdata[0];
                    this.showQuestionsModal(item);
                }
            });
        },

        // 显示题目详情模态框
        showQuestionsModal(item) {
            this.modalTitle = `${item.chapter}: ${item.content}`;
            this.modalContent = item.questions;
            this.showModal = true;
        },

        // 关闭模态框
        closeModal() {
            this.showModal = false;
        },

        // 点击模态框外部关闭
        closeModalOnOutsideClick(event) {
            if (event.target === event.currentTarget) {
                this.closeModal();
            }
        },

        // 文本标准化函数
        normalizeText(text) {
            return text.toLowerCase().replace(/[^\w\s]/g, '').trim();
        },

        // 获取章节颜色
        getChapterColor(index) {
            const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'];
            return colors[index % colors.length];
        },

        // 创建题目类型分布饼图
        async createQuestionTypesChart() {
            try {
                const response = await this.fetchData('/api/question-types');
                const typeCounts = response.data;

                const data = [{
                    type: 'pie',
                    labels: Object.keys(typeCounts),
                    values: Object.values(typeCounts),
                    marker: {
                        colors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
                    },
                    textinfo: 'label+percent',
                    textposition: 'inside',
                    hovertemplate: '<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>'
                }];

                const layout = {
                    title: '',
                    showlegend: true,
                    legend: { orientation: 'h', y: -0.2 },
                    margin: { t: 20, b: 20, l: 20, r: 20 }
                };

                Plotly.newPlot('question-types-chart', data, layout);
            } catch (error) {
                console.error('创建题目类型图表失败:', error);
                // 降级到本地计算
                this.createQuestionTypesChartLocally();
            }
        },

        // 本地创建题目类型分布饼图（降级方案）
        createQuestionTypesChartLocally() {
            const questions = this.questionsData.questions;
            const typeCounts = {};

            questions.forEach(question => {
                const type = question.type || 'Unknown';
                typeCounts[type] = (typeCounts[type] || 0) + 1;
            });

            const data = [{
                type: 'pie',
                labels: Object.keys(typeCounts),
                values: Object.values(typeCounts),
                marker: {
                    colors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
                },
                textinfo: 'label+percent',
                textposition: 'inside',
                hovertemplate: '<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>'
            }];

            const layout = {
                title: '',
                showlegend: true,
                legend: { orientation: 'h', y: -0.2 },
                margin: { t: 20, b: 20, l: 20, r: 20 }
            };

            Plotly.newPlot('question-types-chart', data, layout);
        },

        // 创建知识点热力图
        async createKnowledgeHeatmap() {
            try {
                const response = await this.fetchData('/api/knowledge-heatmap');
                const heatmapData = response.data;

                const kpList = Object.keys(heatmapData.knowledgePoints);
                const chapterList = heatmapData.chapters;

                const z = kpList.map(kp => chapterList.map(chapter => heatmapData.knowledgePoints[kp][chapter] || 0));

                const data = [{
                    type: 'heatmap',
                    x: chapterList.map(c => `Chapter ${c}`),
                    y: kpList,
                    z: z,
                    colorscale: 'YlOrRd',
                    hovertemplate: '知识点: %{y}<br>章节: %{x}<br>题目数: %{z}<extra></extra>'
                }];

                const layout = {
                    title: '',
                    xaxis: { title: '章节' },
                    yaxis: { title: '知识点' },
                    margin: { t: 20, b: 80, l: 100, r: 20 }
                };

                Plotly.newPlot('knowledge-heatmap', data, layout);
            } catch (error) {
                console.error('创建知识点热力图失败:', error);
                // 降级到本地计算
                this.createKnowledgeHeatmapLocally();
            }
        },

        // 本地创建知识点热力图（降级方案）
        createKnowledgeHeatmapLocally() {
            const questions = this.questionsData.questions;
            const knowledgePoints = {};
            const chapters = {};

            questions.forEach(question => {
                const chapter = question.refer ? question.refer.match(/Chapter (\d+)/)?.[1] : 'Unknown';
                if (question.knowledge_points && Array.isArray(question.knowledge_points)) {
                    question.knowledge_points.forEach(kp => {
                        if (!knowledgePoints[kp]) {
                            knowledgePoints[kp] = {};
                        }
                        knowledgePoints[kp][chapter] = (knowledgePoints[kp][chapter] || 0) + 1;
                        chapters[chapter] = true;
                    });
                }
            });

            const kpList = Object.keys(knowledgePoints);
            const chapterList = Object.keys(chapters).sort();

            const z = kpList.map(kp => chapterList.map(chapter => knowledgePoints[kp][chapter] || 0));

            const data = [{
                type: 'heatmap',
                x: chapterList.map(c => `Chapter ${c}`),
                y: kpList,
                z: z,
                colorscale: 'YlOrRd',
                hovertemplate: '知识点: %{y}<br>章节: %{x}<br>题目数: %{z}<extra></extra>'
            }];

            const layout = {
                title: '',
                xaxis: { title: '章节' },
                yaxis: { title: '知识点' },
                margin: { t: 20, b: 80, l: 100, r: 20 }
            };

            Plotly.newPlot('knowledge-heatmap', data, layout);
        },

        // 创建章节重要性柱状图
        async createChapterImportanceChart() {
            try {
                const response = await this.fetchData('/api/chapter-importance');
                const chapterCounts = response.data;

                const chapters = Object.keys(chapterCounts).sort((a, b) => parseInt(a) - parseInt(b));
                const counts = chapters.map(ch => chapterCounts[ch]);

                const data = [{
                    type: 'bar',
                    x: chapters.map(c => `Chapter ${c}`),
                    y: counts,
                    marker: {
                        color: chapters.map((_, i) => this.getChapterColor(i))
                    },
                    hovertemplate: '<b>%{x}</b><br>题目数量: %{y}<extra></extra>'
                }];

                const layout = {
                    title: '',
                    xaxis: { title: '章节' },
                    yaxis: { title: '题目数量' },
                    margin: { t: 20, b: 60, l: 60, r: 20 }
                };

                Plotly.newPlot('chapter-importance-chart', data, layout);
            } catch (error) {
                console.error('创建章节重要性图表失败:', error);
                // 降级到本地计算
                this.createChapterImportanceChartLocally();
            }
        },

        // 本地创建章节重要性柱状图（降级方案）
        createChapterImportanceChartLocally() {
            const questions = this.questionsData.questions;
            const chapterCounts = {};

            questions.forEach(question => {
                if (question.refer) {
                    const chapterMatches = question.refer.match(/Chapter (\d+)/g);
                    if (chapterMatches) {
                        chapterMatches.forEach(match => {
                            const chapterNum = match.match(/Chapter (\d+)/)[1];
                            chapterCounts[chapterNum] = (chapterCounts[chapterNum] || 0) + 1;
                        });
                    }
                }
            });

            const chapters = Object.keys(chapterCounts).sort((a, b) => parseInt(a) - parseInt(b));
            const counts = chapters.map(ch => chapterCounts[ch]);

            const data = [{
                type: 'bar',
                x: chapters.map(c => `Chapter ${c}`),
                y: counts,
                marker: {
                    color: chapters.map((_, i) => this.getChapterColor(i))
                },
                hovertemplate: '<b>%{x}</b><br>题目数量: %{y}<extra></extra>'
            }];

            const layout = {
                title: '',
                xaxis: { title: '章节' },
                yaxis: { title: '题目数量' },
                margin: { t: 20, b: 60, l: 60, r: 20 }
            };

            Plotly.newPlot('chapter-importance-chart', data, layout);
        },

        // 创建题目难度分布图
        createDifficultyDistributionChart() {
            const questions = this.questionsData.questions;
            const difficultyLevels = { 'Easy': 0, 'Medium': 0, 'Hard': 0, 'Unknown': 0 };

            questions.forEach(question => {
                // 基于题目类型或其他特征推断难度
                let difficulty = 'Unknown';
                const type = question.type?.toLowerCase() || '';

                if (type.includes('short') || type.includes('true') || type.includes('multiple')) {
                    difficulty = 'Easy';
                } else if (type.includes('essay') || type.includes('calculation')) {
                    difficulty = 'Hard';
                } else {
                    difficulty = 'Medium';
                }

                difficultyLevels[difficulty]++;
            });

            const data = [{
                type: 'bar',
                x: Object.keys(difficultyLevels),
                y: Object.values(difficultyLevels),
                marker: {
                    color: ['#4CAF50', '#FF9800', '#F44336', '#9E9E9E']
                },
                hovertemplate: '<b>%{x}</b><br>题目数量: %{y}<extra></extra>'
            }];

            const layout = {
                title: '',
                xaxis: { title: '难度等级' },
                yaxis: { title: '题目数量' },
                margin: { t: 20, b: 60, l: 60, r: 20 }
            };

            Plotly.newPlot('difficulty-distribution-chart', data, layout);
        }
    }
}).mount('#app');