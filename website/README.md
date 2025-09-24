# NTU分布式系统考试分析平台

🎓 一个基于 Vue.js + Node.js 的现代化考试数据分析平台

## 架构特点

- **前后端分离**: Vue.js 前端 + Express.js 后端
- **RESTful API**: 提供标准化的数据接口
- **响应式设计**: 支持各种设备访问
- **实时数据**: 支持数据缓存和动态刷新
- **专业可视化**: 基于 Plotly.js 的多维度数据图表

## 技术栈

### 前端
- **Vue.js 3**: 现代化的前端框架
- **Plotly.js**: 专业的数据可视化库
- **HTML5/CSS3**: 现代Web标准

### 后端
- **Node.js**: JavaScript 运行环境
- **Express.js**: Web 应用框架
- **CORS**: 跨域资源共享
- **Helmet**: 安全中间件

## 功能特性

### 📊 数据可视化
- 课程时间线交互图
- 题目类型分布饼图
- 知识点热力图分析
- 章节重要性柱状图
- 题目难度分布图

### � 交互功能
- 点击气泡查看题目详情
- 模态框展示详细信息
- 响应式图表交互

### � 统计分析
- 总题目数量统计
- 题型种类分析
- 知识点覆盖范围
- 章节分布情况

## 快速开始

### 环境要求
- Node.js >= 14.0.0
- npm >= 6.0.0

### 安装依赖

```bash
# 安装后端依赖
cd server
npm install

# 安装前端依赖
cd ..
npm install
```

### 运行应用

#### 开发模式（推荐）
```bash
npm run dev
```
这将同时启动：
- 后端服务器: http://localhost:3001
- 前端服务器: http://localhost:8080

#### 生产模式
```bash
npm start
```

#### 单独启动
```bash
# 只启动后端
npm run server

# 只启动前端
npm run client
```

## API 接口

### 数据接口
- `GET /api/curriculum` - 获取课程结构数据
- `GET /api/questions` - 获取题目数据
- `GET /api/statistics` - 获取统计信息
- `GET /api/question-types` - 获取题目类型分布
- `GET /api/chapter-importance` - 获取章节重要性数据
- `GET /api/knowledge-heatmap` - 获取知识点热力图数据

### 系统接口
- `GET /api/health` - 健康检查
- `POST /api/refresh` - 刷新数据缓存

## 项目结构

```
website/
├── index.html          # 主页面
├── styles.css          # 样式文件
├── app.js             # Vue应用逻辑
├── package.json       # 前端依赖配置
└── server/            # 后端服务器
    ├── index.js       # Express服务器
    └── package.json   # 后端依赖配置
```

## 数据流程

1. **数据加载**: 后端从 `../data/` 和 `../output/` 目录读取JSON数据
2. **API服务**: 提供RESTful API接口给前端调用
3. **前端渲染**: Vue应用通过API获取数据并渲染图表
4. **用户交互**: 用户可以点击图表元素查看详细信息

## 开发说明

### 添加新的可视化图表

1. 在后端添加新的API端点
2. 在前端Vue应用中添加相应的图表创建方法
3. 在HTML中添加图表容器
4. 更新样式文件

### 数据更新

当源数据文件更新时，可以调用 `/api/refresh` 接口刷新缓存。

## 部署说明

### 生产环境部署

1. 确保所有依赖都已安装
2. 设置环境变量（如需要）
3. 运行 `npm start` 启动服务

## 许可证

ISC License