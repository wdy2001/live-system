# 阳光社区生活缴费系统 - 电/水/气费在线缴纳、报修一站式服务平台

一款面向社区居民的一站式公共事业缴费平台，支持电费/水费/燃气费在线缴纳、账单分类查询、阶梯计费规则查看及故障报修。

## 🎯 功能特性

- **电费缴费** — 查询电费欠费账单，在线模拟支付，生成交易凭证
- **水费缴费** — 查询水费欠费账单，在线模拟支付，生成交易凭证
- **燃气缴费** — 查询燃气费欠费账单，在线模拟支付，生成交易凭证
- **分类缴费记录** — 按类型（电/水/气）与状态（待缴/已缴）筛选，账单详情含阶梯计费拆分
- **计费规则展示** — 阶梯电价/水价/气价公开展示，附计算示例
- **故障报修** — 提交报修工单（类型 + 描述 + 紧急程度），跟踪处理进度

## 🏗️ 技术栈

| 层级 | 技术栈 |
|------|--------|
| 后端 | Python 3.10+ / Flask 3 / Flask-JWT-Extended / Flask-SQLAlchemy / PyMySQL / Werkzeug 安全哈希 |
| 前端 | React 18 / TypeScript 5 / Vite 6 / Tailwind CSS / Zustand / Axios / Recharts / lucide-react |
| 数据库 | MySQL 8.x（支持 SQLite 本地开发回退） |

## 📅 10 天里程碑规划

| 阶段 | 时间 | 工作内容 |
|------|------|----------|
| 第一阶段 | Day1-3 | 后端 API 与数据模型 |
| 第二阶段 | Day4-6 | 前端页面与联调 |
| 第三阶段 | Day7-8 | 数据库脚本与种子数据 |
| 第四阶段 | Day9 | 构建部署与 GitHub 上传 |
| 第五阶段 | Day10 | 整体验收与修复 |

## 🚀 快速开始

### SQLite 模式（0 配置推荐体验）

适合快速体验和开发测试，无需安装 MySQL，3 步即可启动。

```bash
# 1. 安装依赖
pip install -r backend/requirements.txt
npm install

# 2. 初始化种子数据
cd backend && USE_SQLITE=true python seed.py

# 3. 启动服务
# 后端（端口 5000）
cd backend && USE_SQLITE=true python app.py
# 前端（新开终端，端口 5173）
npm run dev
```

访问 http://localhost:5173 即可使用。

### MySQL 模式

适用于生产环境或需要 MySQL 特性的场景，4 步启动。

```bash
# 0. 安装 MySQL 8.x 并创建用户/授权
mysql -u root -e "CREATE DATABASE IF NOT EXISTS life_system DEFAULT CHARSET utf8mb4;"
mysql -u root -e "CREATE USER 'life_app'@'localhost' IDENTIFIED BY 'life_pass_2026'; \
                  GRANT ALL PRIVILEGES ON life_system.* TO 'life_app'@'localhost'; FLUSH PRIVILEGES;"

# 1. 导入数据库 schema
mysql -u root < backend/schema.sql

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填写 DB_USER 和 DB_PASSWORD

# 3. 安装依赖
pip install -r backend/requirements.txt
npm install

# 4. 启动服务
# 初始化种子数据
cd backend && python seed.py
# 启动后端（端口 5000）
cd backend && python app.py
# 启动前端（新开终端，端口 5173）
npm run dev
```

## 🔐 演示账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 居民 | demo | demo123 |
| 管理员 | admin | admin123 |

## 📂 目录结构

```
/workspace
├── backend/
│   ├── app.py                    # Flask 应用入口
│   ├── config.py                 # 配置（数据库/JWT）
│   ├── extensions.py             # db / jwt 扩展实例
│   ├── models.py                 # SQLAlchemy 数据模型
│   ├── schema.sql                # MySQL 建表脚本
│   ├── seed.py                   # 种子数据脚本
│   ├── routes/
│   │   ├── auth.py               # 注册/登录/鉴权
│   │   ├── bills.py              # 账单查询/支付
│   │   ├── dashboard.py          # 工作台概览
│   │   ├── households.py         # 户号管理
│   │   ├── repairs.py            # 故障报修
│   │   └── rules.py              # 计费规则
│   └── services/
│       └── billing.py            # 阶梯计费算法
├── src/
│   ├── App.tsx                   # 应用根组件
│   ├── main.tsx                  # React 入口
│   ├── pages/
│   │   ├── AuthLayout.tsx        # 登录/注册布局
│   │   ├── Dashboard.tsx         # 工作台
│   │   ├── Login.tsx             # 登录页
│   │   ├── Payment.tsx           # 缴费中心
│   │   ├── Records.tsx           # 缴费记录
│   │   ├── Register.tsx          # 注册页
│   │   ├── Repair.tsx            # 故障报修
│   │   └── Rules.tsx             # 计费规则
│   ├── components/
│   │   ├── Layout.tsx            # 主布局
│   │   ├── Skeleton.tsx          # 骨架屏
│   │   ├── StatCard.tsx          # 统计卡片
│   │   ├── TypeBadge.tsx         # 类型标签
│   │   └── UsageChart.tsx        # 用量图表
│   ├── store/
│   │   └── auth.ts               # Zustand 状态管理
│   └── lib/
│       ├── api.ts                # Axios API 封装
│       ├── constants.tsx         # 常量定义
│       └── utils.ts              # 工具函数
├── public/                       # 静态资源（favicon 等）
├── dist/                         # 前端构建产物
└── README.md                     # 本说明文档
```

## 🧭 功能模块与路由映射

| 页面路径 | 页面名称 | 对应 API | 功能说明 |
|----------|----------|----------|----------|
| / | 工作台 Dashboard | /api/dashboard | 数据概览：待缴总额、本月用量、报修进度、近 6 月用量趋势 |
| /payment | 缴费中心 | /api/bills + /api/bills/:id/pay | 按费用类型查询欠费账单并完成支付 |
| /records | 缴费记录 | /api/bills | 按类型和状态筛选历史账单，查看阶梯计费详情 |
| /rules | 计费规则 | /api/rules | 展示电/水/气阶梯计费规则及计算示例 |
| /repair | 故障报修 | /api/repairs | 提交报修工单并跟踪处理进度 |
| /login | 登录 | /api/auth/login | 用户登录获取 JWT Token |
| /register | 注册 | /api/auth/register | 新用户注册账号 |

## 声明

本项目用于学习演示。
