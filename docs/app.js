// 全局变量
let curriculumData = null;
let questionsData = null;

// Application initialization
async function initApp() {
    try {
        console.log('Starting to load data...');
        showLoading();

        // Load curriculum data
        console.log('Loading curriculum data...');
        const curriculumResponse = await fetch('../data/curriculum.json');
        if (!curriculumResponse.ok) {
            throw new Error(`Failed to load curriculum data: ${curriculumResponse.status}`);
        }
        curriculumData = await curriculumResponse.json();
        console.log('Curriculum data loaded successfully:', curriculumData);

        // Load question data
        console.log('Loading question data...');
        const questionsResponse = await fetch('../output/extended_questions.json');
        if (!questionsResponse.ok) {
            throw new Error(`Failed to load question data: ${questionsResponse.status}`);
        }
        questionsData = await questionsResponse.json();
        console.log('Question data loaded successfully:', questionsData);

        // Generate statistics
        generateStats();

        // Create visualizations
        createVisualizations();

        // Create timeline
        setTimeout(() => {
            createTimeline();
        }, 100);

        hideLoading();
        showMainContent();
        console.log('Application initialization completed');

    } catch (error) {
        console.error('Data loading failed:', error);
        showError(error.message);
    }
}

// 显示加载状态
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('error').style.display = 'none';
    document.getElementById('main-content').style.display = 'none';
}

// 隐藏加载状态
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// 显示错误状态
function showError(message) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('main-content').style.display = 'none';
    document.getElementById('error').style.display = 'block';
    document.getElementById('error-message').textContent = message;
}

// 显示主内容
function showMainContent() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error').style.display = 'none';
    document.getElementById('main-content').style.display = 'block';
}

// Generate statistics
function generateStats() {
    const questions = questionsData.questions;
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

    const stats = [
        { number: totalQuestions, label: 'Total Questions' },
        { number: uniqueTypes, label: 'Question Types' },
        { number: uniqueKnowledgePoints, label: 'Knowledge Points' },
        { number: chaptersCovered, label: 'Chapters Covered' }
    ];

    renderStats(stats);
}

// Render statistics
function renderStats(stats) {
    const statsGrid = document.getElementById('stats-grid');
    statsGrid.innerHTML = '';

    stats.forEach(stat => {
        const statCard = document.createElement('div');
        statCard.className = 'stat-card';
        statCard.innerHTML = `
            <div class="stat-number">${stat.number}</div>
            <div class="stat-label">${stat.label}</div>
        `;
        statsGrid.appendChild(statCard);
    });
}

// Create timeline
function createTimeline() {
    const chapters = curriculumData.distributedSystemsCurriculum;
    const questions = questionsData.questions;

    // 准备时间线数据
    const timelineData = [];

    chapters.forEach((chapter, chapterIndex) => {
        const chapterNumber = chapter.chapterNumber;
        const chapterTitle = chapter.chapterTitle;
        const contentItems = chapter.content;

        if (contentItems && contentItems.length > 0) {
            contentItems.forEach((content, contentIndex) => {
                // 找到与此知识点相关的题目
                const relatedQuestions = questions.filter(question => {
                    if (!question.knowledge_points || !Array.isArray(question.knowledge_points)) {
                        return false;
                    }
                    return question.knowledge_points.some(kp =>
                        normalizeText(content).includes(normalizeText(kp)) ||
                        normalizeText(kp).includes(normalizeText(content))
                    );
                });

                timelineData.push({
                    chapter: `Chapter ${chapterNumber}`,
                    chapterTitle: chapterTitle,
                    content: content,
                    questions: relatedQuestions,
                    questionCount: relatedQuestions.length,
                    color: getChapterColor(chapterIndex)
                });
            });
        }
    });

    // 创建自定义时间线HTML
    createCustomTimeline(timelineData, chapters);
}

// 创建自定义时间线
function createCustomTimeline(timelineData, chapters) {
    const timelineContainer = document.getElementById('timeline');
    timelineContainer.innerHTML = '';

    // 创建纵向时间线容器
    const timelineWrapper = document.createElement('div');
    timelineWrapper.className = 'timeline-vertical-wrapper';
    timelineContainer.appendChild(timelineWrapper);

    // 分组数据按章节
    const chapterGroups = {};
    timelineData.forEach(item => {
        if (!chapterGroups[item.chapter]) {
            chapterGroups[item.chapter] = [];
        }
        chapterGroups[item.chapter].push(item);
    });

    // 为每个章节创建纵向区域
    Object.keys(chapterGroups).forEach((chapterKey, chapterIndex) => {
        const chapterItems = chapterGroups[chapterKey];

        // 创建章节区域
        const chapterSection = document.createElement('div');
        chapterSection.className = 'chapter-section-vertical';
        chapterSection.style.background = `linear-gradient(135deg, ${getChapterColor(chapterIndex)}10, ${getChapterColor(chapterIndex)}05)`;
        chapterSection.style.borderLeft = `4px solid ${getChapterColor(chapterIndex)}`;

        // 添加章节节点
        const chapterNode = document.createElement('div');
        chapterNode.className = 'chapter-node';
        chapterNode.textContent = chapterKey;  // 显示 "Chapter 1" 而不是 "1"
        chapterNode.style.background = getChapterColor(chapterIndex);
        chapterSection.appendChild(chapterNode);

        // 创建章节内容
        const chapterContent = document.createElement('div');
        chapterContent.className = 'chapter-content';

        // 添加章节标题
        const chapterTitle = document.createElement('div');
        chapterTitle.className = 'chapter-title';
        chapterTitle.textContent = chapterItems[0].chapterTitle;
        chapterContent.appendChild(chapterTitle);

        // 创建知识点网格
        const knowledgeGrid = document.createElement('div');
        knowledgeGrid.className = 'knowledge-points-grid';

        // 为每个知识点创建气泡
        chapterItems.forEach((item, itemIndex) => {
            if (item.questionCount > 0) {
                const bubble = document.createElement('button');
                bubble.className = 'knowledge-bubble';
                bubble.style.borderColor = item.color;
                bubble.style.background = `rgba(${hexToRgb(item.color)}, 0.1)`;

                // 添加工具提示
                const tooltip = document.createElement('div');
                tooltip.className = 'bubble-tooltip';
                tooltip.textContent = `${item.content} (${item.questionCount}个题目)`;
                bubble.appendChild(tooltip);

                const bubbleTitle = document.createElement('div');
                bubbleTitle.className = 'bubble-title';
                bubbleTitle.textContent = item.content;

                const bubbleCount = document.createElement('div');
                bubbleCount.className = 'bubble-count';
                bubbleCount.textContent = item.questionCount;

                bubble.appendChild(bubbleTitle);
                bubble.appendChild(bubbleCount);

                // 添加点击事件
                bubble.addEventListener('click', () => {
                    showQuestionsModal(item);
                });

                knowledgeGrid.appendChild(bubble);
            }
        });

        chapterContent.appendChild(knowledgeGrid);
        chapterSection.appendChild(chapterContent);
        timelineWrapper.appendChild(chapterSection);
    });
}

// 显示题目详情模态框
function showQuestionsModal(item) {
    const modal = document.getElementById('question-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');

    modalTitle.textContent = `${item.chapter}: ${item.content}`;
    modalBody.innerHTML = '';

    if (item.questions.length === 0) {
        modalBody.innerHTML = '<p>No related questions found for this knowledge point</p>';
    } else {
        item.questions.forEach(question => {
            const questionCard = document.createElement('div');
            questionCard.className = 'question-card';

            const typeClass = `type-${question.type.replace(/\s+/g, '')}`;
            const knowledgePointsHtml = question.knowledge_points && Array.isArray(question.knowledge_points) && question.knowledge_points.length > 0
                ? `<div class="knowledge-points"><strong>Knowledge Points:</strong> ${question.knowledge_points.join('; ')}</div>`
                : '';

            questionCard.innerHTML = `
                <span class="question-type ${typeClass}">${question.type}</span>
                <div class="question-title">${question.title}</div>
                <div class="question-meta">
                    <strong>Source:</strong> ${question.source} | <strong>Chapter:</strong> ${question.refer}
                </div>
                ${knowledgePointsHtml}
            `;

            modalBody.appendChild(questionCard);
        });
    }

    modal.style.display = 'block';
}

// 关闭模态框
function closeModal() {
    document.getElementById('question-modal').style.display = 'none';
}

// 点击模态框外部关闭
window.onclick = function (event) {
    const modal = document.getElementById('question-modal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

// 文本标准化函数
function normalizeText(text) {
    return text.toLowerCase().replace(/[^\w\s]/g, '').trim();
}

// 获取章节颜色
function getChapterColor(index) {
    const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'];
    return colors[index % colors.length];
}

// 将十六进制颜色转换为RGB
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : null;
}

// 创建数据可视化
function createVisualizations() {
    const visualizationGrid = document.getElementById('visualization-grid');
    visualizationGrid.innerHTML = '';

    // 紧凑的知识点导航 (放在首位)
    const compactHeatmapCard = createVisualizationCard('🗺️ Compact Knowledge Navigator', 'Efficient knowledge point exploration with coverage status');
    compactHeatmapCard.appendChild(createCompactHeatmap());
    visualizationGrid.appendChild(compactHeatmapCard);

    // 知识点重要性分析
    const importanceCard = createVisualizationCard('🎯 Knowledge Point Importance', 'Identify key topics based on question frequency');
    importanceCard.appendChild(createImportanceAnalysis());
    visualizationGrid.appendChild(importanceCard);

    // 章节难度分布
    const difficultyCard = createVisualizationCard('📊 Chapter Difficulty Distribution', 'Understanding chapter complexity through data');
    difficultyCard.appendChild(createDifficultyDistribution());
    visualizationGrid.appendChild(difficultyCard);

    // 题目类型分布矩阵
    const typeMatrixCard = createVisualizationCard('🔍 Question Type Matrix', 'Question types across chapters');
    typeMatrixCard.appendChild(createQuestionTypeMatrix());
    visualizationGrid.appendChild(typeMatrixCard);
}

// 创建可视化卡片
function createVisualizationCard(title, description) {
    const card = document.createElement('div');
    card.className = 'visualization-card';

    const titleElement = document.createElement('h3');
    titleElement.textContent = title;

    const descElement = document.createElement('p');
    descElement.textContent = description;
    descElement.style.fontSize = '0.9rem';
    descElement.style.color = 'var(--text-muted)';
    descElement.style.marginBottom = '15px';

    card.appendChild(titleElement);
    card.appendChild(descElement);

    return card;
}

// 创建知识点重要性分析
function createImportanceAnalysis() {
    const container = document.createElement('div');
    container.className = 'importance-analysis';

    // 计算每个知识点的题目数量
    const knowledgePointStats = {};

    curriculumData.distributedSystemsCurriculum.forEach(chapter => {
        chapter.content.forEach(content => {
            const relatedQuestions = questionsData.questions.filter(question => {
                if (!question.knowledge_points || !Array.isArray(question.knowledge_points)) {
                    return false;
                }
                return question.knowledge_points.some(kp =>
                    normalizeText(content).includes(normalizeText(kp)) ||
                    normalizeText(kp).includes(normalizeText(content))
                );
            });

            knowledgePointStats[content] = {
                count: relatedQuestions.length,
                chapter: chapter.chapterNumber,
                chapterTitle: chapter.chapterTitle
            };
        });
    });

    // 按重要性排序
    const sortedPoints = Object.entries(knowledgePointStats)
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 10); // 只显示前10个

    sortedPoints.forEach(([point, data]) => {
        const item = document.createElement('div');
        item.className = 'importance-item';

        const pointInfo = document.createElement('div');
        pointInfo.className = 'point-info';

        const pointText = document.createElement('div');
        pointText.className = 'point-text';
        pointText.textContent = point;

        const chapterBadge = document.createElement('div');
        chapterBadge.className = 'chapter-badge';
        chapterBadge.textContent = `Ch.${data.chapter}`;

        pointInfo.appendChild(pointText);
        pointInfo.appendChild(chapterBadge);

        const importanceBar = document.createElement('div');
        importanceBar.className = 'importance-bar';

        const barFill = document.createElement('div');
        barFill.className = 'bar-fill';
        barFill.style.width = `${(data.count / Math.max(...sortedPoints.map(p => p[1].count))) * 100}%`;

        const countLabel = document.createElement('div');
        countLabel.className = 'count-label';
        countLabel.textContent = data.count;

        importanceBar.appendChild(barFill);
        importanceBar.appendChild(countLabel);

        item.appendChild(pointInfo);
        item.appendChild(importanceBar);
        container.appendChild(item);
    });

    return container;
}

// 创建章节难度分布
function createDifficultyDistribution() {
    const container = document.createElement('div');
    container.className = 'difficulty-distribution';

    curriculumData.distributedSystemsCurriculum.forEach((chapter, index) => {
        const chapterItem = document.createElement('div');
        chapterItem.className = 'difficulty-item';

        const chapterHeader = document.createElement('div');
        chapterHeader.className = 'chapter-header';

        const chapterTitle = document.createElement('div');
        chapterTitle.className = 'chapter-title-compact';
        chapterTitle.textContent = `Chapter ${chapter.chapterNumber}`;

        const metrics = document.createElement('div');
        metrics.className = 'chapter-metrics';

        // 计算章节的各种指标
        const questionCount = questionsData.questions.filter(q =>
            q.refer && q.refer.includes(`Chapter ${chapter.chapterNumber}`)
        ).length;

        const knowledgePoints = chapter.content.length;
        const avgQuestionsPerPoint = knowledgePoints > 0 ? (questionCount / knowledgePoints).toFixed(1) : 0;

        metrics.innerHTML = `
            <span class="metric">📝 ${questionCount} questions</span>
            <span class="metric">🎯 ${knowledgePoints} topics</span>
            <span class="metric">📊 ${avgQuestionsPerPoint} avg</span>
        `;

        chapterHeader.appendChild(chapterTitle);
        chapterHeader.appendChild(metrics);

        const difficultyBar = document.createElement('div');
        difficultyBar.className = 'difficulty-bar';

        // 基于题目数量和知识点密度计算难度
        const difficulty = Math.min(100, (questionCount * 2) + (avgQuestionsPerPoint * 10));
        const barFill = document.createElement('div');
        barFill.className = 'difficulty-fill';
        barFill.style.width = `${difficulty}%`;
        barFill.style.background = getChapterColor(index);

        difficultyBar.appendChild(barFill);

        chapterItem.appendChild(chapterHeader);
        chapterItem.appendChild(difficultyBar);
        container.appendChild(chapterItem);
    });

    return container;
}

// 创建题目类型矩阵
function createQuestionTypeMatrix() {
    const container = document.createElement('div');
    container.className = 'question-type-matrix';

    const types = ['Essay', 'Calculation', 'Fill in Blank', 'Short Answer', 'Programming'];
    const chapters = curriculumData.distributedSystemsCurriculum;

    // 创建矩阵头部
    const header = document.createElement('div');
    header.className = 'matrix-header';

    const emptyCell = document.createElement('div');
    emptyCell.className = 'matrix-cell matrix-corner';
    header.appendChild(emptyCell);

    chapters.forEach(chapter => {
        const chapterCell = document.createElement('div');
        chapterCell.className = 'matrix-cell matrix-chapter';
        chapterCell.textContent = `Ch.${chapter.chapterNumber}`;
        header.appendChild(chapterCell);
    });

    container.appendChild(header);

    // 创建矩阵行
    types.forEach(type => {
        const row = document.createElement('div');
        row.className = 'matrix-row';

        const typeCell = document.createElement('div');
        typeCell.className = 'matrix-cell matrix-type';
        typeCell.textContent = type;
        row.appendChild(typeCell);

        chapters.forEach(chapter => {
            const count = questionsData.questions.filter(q => {
                if (!q.refer || q.type !== type) return false;
                // 解析refer字段中的章节信息
                const chapterMatches = q.refer.match(/Chapter (\d+)/g);
                if (!chapterMatches) return false;
                return chapterMatches.some(match => {
                    const chapterNum = match.match(/Chapter (\d+)/)[1];
                    return chapterNum === chapter.chapterNumber;
                });
            }).length;

            const dataCell = document.createElement('div');
            dataCell.className = `matrix-cell matrix-data ${count > 0 ? 'has-data' : 'no-data'}`;
            dataCell.textContent = count > 0 ? count : '';
            dataCell.title = `${type} questions in Chapter ${chapter.chapterNumber}: ${count}`;

            row.appendChild(dataCell);
        });

        container.appendChild(row);
    });

    return container;
}

// 创建紧凑的知识点导航
function createCompactHeatmap() {
    const container = document.createElement('div');
    container.className = 'compact-heatmap';

    curriculumData.distributedSystemsCurriculum.forEach((chapter, chapterIndex) => {
        const chapterSection = document.createElement('div');
        chapterSection.className = 'compact-chapter';

        const chapterHeader = document.createElement('div');
        chapterHeader.className = 'compact-chapter-header';
        chapterHeader.textContent = `Chapter ${chapter.chapterNumber}`;
        chapterHeader.style.borderLeftColor = getChapterColor(chapterIndex);

        chapterSection.appendChild(chapterHeader);

        const pointsGrid = document.createElement('div');
        pointsGrid.className = 'compact-points-grid';

        chapter.content.forEach((content, contentIndex) => {
            const point = document.createElement('div');
            point.className = 'compact-point';

            // 计算这个知识点的题目数量
            const questionCount = questionsData.questions.filter(question => {
                if (!question.knowledge_points || !Array.isArray(question.knowledge_points)) {
                    return false;
                }
                return question.knowledge_points.some(kp =>
                    normalizeText(content).includes(normalizeText(kp)) ||
                    normalizeText(kp).includes(normalizeText(content))
                );
            }).length;

            // 根据题目数量设置强度，没有题目的用特殊样式
            if (questionCount === 0) {
                point.className = 'compact-point no-questions';
            } else {
                const intensity = Math.min(5, Math.max(1, Math.ceil(questionCount / 2)));
                point.className = `compact-point intensity-${intensity}`;
            }

            point.textContent = content.length > 20 ? content.substring(0, 17) + '...' : content;
            point.title = questionCount > 0 ? `${content} (${questionCount} questions)` : `${content} (No questions yet)`;

            point.addEventListener('click', () => {
                showKnowledgePointModal(chapter, content);
            });

            pointsGrid.appendChild(point);
        });

        chapterSection.appendChild(pointsGrid);
        container.appendChild(chapterSection);
    });

    return container;
}

// 显示知识点详情模态框
function showKnowledgePointModal(chapter, content) {
    const modal = document.getElementById('question-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');

    modalTitle.textContent = `Chapter ${chapter.chapterNumber}: ${content}`;

    // 查找相关题目
    const relatedQuestions = questionsData.questions.filter(question => {
        if (!question.knowledge_points || !Array.isArray(question.knowledge_points)) {
            return false;
        }
        return question.knowledge_points.some(kp =>
            normalizeText(content).includes(normalizeText(kp)) ||
            normalizeText(kp).includes(normalizeText(content))
        );
    });

    modalBody.innerHTML = `
        <div style="margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 8px;">
            <h4 style="margin: 0 0 10px 0; color: var(--primary-color);">📖 Knowledge Point Details</h4>
            <p style="margin: 0; color: var(--text-muted);"><strong>Chapter:</strong> ${chapter.chapterTitle}</p>
            <p style="margin: 5px 0 0 0; color: var(--text-muted);"><strong>Content:</strong> ${content}</p>
        </div>
    `;

    if (relatedQuestions.length === 0) {
        modalBody.innerHTML += '<p style="text-align: center; color: var(--text-muted);">No related questions found for this knowledge point</p>';
    } else {
        modalBody.innerHTML += `<h4 style="color: var(--primary-color); margin-bottom: 15px;">📝 Related Questions (${relatedQuestions.length})</h4>`;
        relatedQuestions.forEach(question => {
            const questionCard = document.createElement('div');
            questionCard.className = 'question-card';

            const typeClass = `type-${question.type.replace(/\s+/g, '')}`;
            const knowledgePointsHtml = question.knowledge_points && Array.isArray(question.knowledge_points) && question.knowledge_points.length > 0
                ? `<div class="knowledge-points"><strong>Knowledge Points:</strong> ${question.knowledge_points.join('; ')}</div>`
                : '';

            questionCard.innerHTML = `
                <span class="question-type ${typeClass}">${question.type}</span>
                <div class="question-title">${question.title}</div>
                <div class="question-meta">
                    <strong>Source:</strong> ${question.source} | <strong>Chapter:</strong> ${question.refer}
                </div>
                ${knowledgePointsHtml}
            `;

            modalBody.appendChild(questionCard);
        });
    }

    modal.style.display = 'block';
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', initApp);