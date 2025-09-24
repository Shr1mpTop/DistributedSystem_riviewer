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

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', initApp);